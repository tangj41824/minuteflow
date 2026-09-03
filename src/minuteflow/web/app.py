"""FastAPI application for the local MinuteFlow web UI."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi import Path as ApiPath
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from minuteflow import __version__
from minuteflow.agents.backend import AgentBackend, OpenAIAgentsBackend
from minuteflow.config import DEFAULT_MAX_INPUT_CHARS, Settings
from minuteflow.orchestration import MinuteFlowPipeline
from minuteflow.renderers import render_json, render_markdown
from minuteflow.schemas import PipelineEvent
from minuteflow.web.history import HistoryStore
from minuteflow.web.models import HealthResponse, RunCreateRequest, RunDetail, RunSummary
from minuteflow.web.state import RunState, WebServerState

RunIdPath = ApiPath(pattern=r"^[0-9a-f]{32}$")

_HEARTBEAT_SECONDS = 15.0


def _sse_frame(index: int, event: PipelineEvent) -> str:
    return f"id: {index}\nevent: pipeline\ndata: {event.model_dump_json()}\n\n"


def _detail_for(run: RunState, terminal: PipelineEvent | None) -> RunDetail:
    return RunDetail(
        run_id=run.run_id,
        created_at=run.created_at,
        status=run.status,
        meeting_date=run.meeting_date,
        source_text=run.source_text if run.status != "running" else None,
        events=[*run.events, *([terminal] if terminal else [])],
        report=run.report,
        error=run.error,
    )


async def _run_pipeline(server: WebServerState, run: RunState) -> None:
    """Drive one run and publish its events; terminal events are held until durable."""

    async def emit(event: PipelineEvent) -> None:
        if event.stage in ("delivered", "failed"):
            run.pending_terminal = event
        else:
            run.events.append(event)
            run.queue.put_nowait(event)

    try:
        async with server.semaphore:
            report = await server.pipeline.run(
                run.source_text,
                meeting_date=run.meeting_date,
                on_event=emit,
            )
        run.status = "delivered"
        run.report = report
    except Exception as exc:  # noqa: BLE001 - surface any failure as a failed run
        run.status = "failed"
        run.error = str(exc)
    if run.pending_terminal is None:
        run.pending_terminal = PipelineEvent(
            stage=run.status,  # type: ignore[arg-type]
            timestamp=datetime.now(UTC),
            retry_count=run.report.retry_count if run.report else 0,
            message=run.error,
        )
    terminal = run.pending_terminal
    await server.history.save_run(_detail_for(run, terminal))
    run.events.append(terminal)
    run.queue.put_nowait(terminal)
    run.queue.put_nowait(None)
    server.active.pop(run.run_id, None)


def create_app(
    *,
    backend: AgentBackend | None = None,
    settings: Settings | None = None,
    history_dir: Path,
    max_concurrent_runs: int = 2,
    history_max_runs: int = 50,
    frontend_dist: Path | None = None,
) -> FastAPI:
    """Build the web app. Supply ``backend`` (tests) or ``settings`` (live server)."""

    if backend is None and settings is None:
        raise ValueError("create_app requires either backend or settings.")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved_backend = backend or OpenAIAgentsBackend(settings)  # type: ignore[arg-type]
        server = WebServerState(
            backend=resolved_backend,
            pipeline=MinuteFlowPipeline(
                resolved_backend,
                max_input_chars=settings.max_input_chars if settings else DEFAULT_MAX_INPUT_CHARS,
            ),
            settings=settings,
            history=HistoryStore(history_dir, max_runs=history_max_runs),
            max_concurrent_runs=max_concurrent_runs,
            max_input_chars=settings.max_input_chars if settings else DEFAULT_MAX_INPUT_CHARS,
            semaphore=asyncio.Semaphore(max_concurrent_runs),
        )
        app.state.web = server
        yield
        for run in server.active.values():
            if run.task is not None:
                run.task.cancel()
        tasks = [run.task for run in server.active.values() if run.task is not None]
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="MinuteFlow", version=__version__, lifespan=lifespan)

    async def spawn_run(
        text: str,
        *,
        meeting_date: date | None,
        filename: str | None,
        request: Request,
    ) -> JSONResponse:
        server: WebServerState = request.app.state.web
        if len(server.active) >= server.max_concurrent_runs:
            raise HTTPException(
                status_code=429,
                detail=f"Too many concurrent runs (max {server.max_concurrent_runs}).",
            )
        run = RunState(
            run_id=uuid4().hex,
            created_at=datetime.now(UTC),
            meeting_date=meeting_date,
            filename=filename,
            source_text=text,
        )
        server.active[run.run_id] = run
        run.task = asyncio.create_task(_run_pipeline(server, run))
        return JSONResponse(
            status_code=202,
            content={
                "run_id": run.run_id,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
            },
        )

    @app.post("/api/runs", status_code=202)
    async def create_run(body: RunCreateRequest, request: Request) -> JSONResponse:
        return await spawn_run(
            body.text,
            meeting_date=body.meeting_date,
            filename=body.filename,
            request=request,
        )

    @app.post("/api/runs/upload", status_code=202)
    async def upload_run(
        file: Annotated[UploadFile, File()],
        meeting_date: Annotated[date | None, Form()] = None,
        request: Request = None,
    ) -> JSONResponse:
        server: WebServerState = request.app.state.web
        raw = await file.read(server.max_input_chars + 1)
        if len(raw) > server.max_input_chars:
            raise HTTPException(status_code=413, detail="File exceeds the maximum input size.")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
        return await spawn_run(
            text,
            meeting_date=meeting_date,
            filename=file.filename,
            request=request,
        )

    @app.get("/api/runs/{run_id}/events")
    async def stream_events(
        run_id: str = RunIdPath,
        after: int = Query(default=0, ge=0),
        request: Request = None,
    ) -> StreamingResponse:
        server: WebServerState = request.app.state.web
        run = server.active.get(run_id)
        stored = server.history.load_run(run_id) if run is None else None
        if run is None and stored is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        async def event_stream() -> AsyncIterator[str]:
            if run is not None:
                snapshot = run.events[after:]
                # Replay and the queue hold the SAME event instances, so skip queue
                # items already delivered by the replay to avoid double delivery.
                seen = {id(event) for event in snapshot}
                next_id = after
                for event in snapshot:
                    yield _sse_frame(next_id, event)
                    next_id += 1
                while True:
                    try:
                        item = await asyncio.wait_for(run.queue.get(), timeout=_HEARTBEAT_SECONDS)
                    except TimeoutError:
                        yield ": ping\n\n"
                        continue
                    if item is None:
                        break
                    if id(item) in seen:
                        continue
                    seen.add(id(item))
                    yield _sse_frame(next_id, item)
                    next_id += 1
                return
            assert stored is not None
            for index, event in enumerate(stored.events[after:], start=after):
                yield _sse_frame(index, event)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str = RunIdPath, request: Request = None) -> RunDetail:
        server: WebServerState = request.app.state.web
        run = server.active.get(run_id)
        if run is not None:
            return _detail_for(run, None)
        stored = server.history.load_run(run_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return stored

    @app.get("/api/runs")
    async def list_runs(request: Request) -> dict[str, list[RunSummary]]:
        server: WebServerState = request.app.state.web
        return {"runs": server.history.list_runs()}

    @app.delete("/api/runs/{run_id}", status_code=204)
    async def delete_run(run_id: str = RunIdPath, request: Request = None) -> Response:
        server: WebServerState = request.app.state.web
        if run_id in server.active:
            raise HTTPException(status_code=409, detail="Run is still in progress.")
        if not await server.history.delete_run(run_id):
            raise HTTPException(status_code=404, detail="Run not found.")
        return Response(status_code=204)

    @app.get("/api/runs/{run_id}/export")
    async def export_run(
        run_id: str = RunIdPath,
        format: Literal["markdown", "json"] = Query(default="markdown"),
        request: Request = None,
    ) -> Response:
        server: WebServerState = request.app.state.web
        stored = server.history.load_run(run_id)
        if stored is None or stored.report is None:
            raise HTTPException(status_code=404, detail="Run has no finished report.")
        if format == "markdown":
            content, media_type, extension = render_markdown(stored.report), "text/markdown", "md"
        else:
            content, media_type, extension = render_json(stored.report), "application/json", "json"
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="minuteflow-{run_id}.{extension}"'
            },
        )

    @app.get("/api/health")
    async def health(request: Request) -> HealthResponse:
        server: WebServerState = request.app.state.web
        if server.settings is None:
            model = "scripted"
            api_key_configured = False
        else:
            model = server.settings.model
            api_key_configured = bool(server.settings.api_key or os.getenv("OPENAI_API_KEY"))
        return HealthResponse(
            status="ok",
            version=__version__,
            model=model,
            api_key_configured=api_key_configured,
            max_input_chars=server.max_input_chars,
            max_concurrent_runs=server.max_concurrent_runs,
            history_dir=str(server.history.directory),
        )

    if frontend_dist is not None and (frontend_dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(frontend_dist / "index.html")
    else:

        @app.get("/", include_in_schema=False)
        async def index() -> JSONResponse:
            return JSONResponse(
                {
                    "detail": (
                        "Frontend not built. Run `npm run build` in frontend/ "
                        "or use the Vite dev server."
                    )
                }
            )

    return app
