"""Uvicorn bootstrap for ``minuteflow web``."""

from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

import uvicorn

from minuteflow.config import Settings
from minuteflow.web.app import create_app


def resolve_frontend_dist() -> Path | None:
    override = os.getenv("MINUTEFLOW_FRONTEND_DIST")
    if override:
        return Path(override)
    candidate = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if (candidate / "index.html").exists():
        return candidate
    return None


def serve(
    settings: Settings,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = False,
    history_dir: Path | None = None,
) -> int:
    resolved_history = (
        history_dir
        or Path(os.getenv("MINUTEFLOW_HISTORY_DIR", "~/.minuteflow/history")).expanduser()
    )
    app = create_app(
        settings=settings,
        history_dir=resolved_history,
        frontend_dist=resolve_frontend_dist(),
    )
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=[f"http://{host}:{port}"]).start()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    return 0 if uvicorn.Server(config).run() else 1
