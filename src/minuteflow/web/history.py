"""Local JSON-file history for delivered and failed runs (not a database)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from minuteflow.web.models import RunDetail, RunSummary

INDEX_VERSION = 1


class HistoryStore:
    """Persist one JSON file per run plus a small index under a local directory."""

    def __init__(self, directory: Path, *, max_runs: int = 50) -> None:
        self.directory = directory
        self.max_runs = max_runs
        self._lock = asyncio.Lock()
        self.directory.mkdir(parents=True, exist_ok=True)

    @property
    def index_path(self) -> Path:
        return self.directory / "index.json"

    def _run_path(self, run_id: str) -> Path:
        return self.directory / f"{run_id}.json"

    def _read_index(self) -> list[RunSummary]:
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # A missing or corrupt index must not take the server down; it rebuilds lazily.
            return []
        try:
            return [RunSummary.model_validate(item) for item in raw.get("runs", [])]
        except ValueError:
            return []

    def _write_index(self, runs: list[RunSummary]) -> None:
        payload = {
            "version": INDEX_VERSION,
            "runs": [entry.model_dump(mode="json") for entry in runs],
        }
        tmp = self.directory / "index.json.tmp"
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.index_path)

    def list_runs(self) -> list[RunSummary]:
        return self._read_index()

    def load_run(self, run_id: str) -> RunDetail | None:
        try:
            return RunDetail.model_validate_json(self._run_path(run_id).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    async def save_run(self, run: RunDetail) -> None:
        async with self._lock:
            tmp = self._run_path(run.run_id).with_suffix(".json.tmp")
            tmp.write_text(run.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp, self._run_path(run.run_id))
            summary = RunSummary(
                run_id=run.run_id,
                created_at=run.created_at,
                status=run.status,
                meeting_date=run.meeting_date,
                summary=run.report.summary if run.report else None,
                retry_count=run.report.retry_count if run.report else None,
                error=run.error,
            )
            runs = [summary] + [entry for entry in self._read_index() if entry.run_id != run.run_id]
            self._prune(runs[: self.max_runs])

    def _prune(self, keep: list[RunSummary]) -> None:
        keep_ids = {entry.run_id for entry in keep}
        for path in self.directory.glob("*.json"):
            if path.name == "index.json" or path.name.endswith(".tmp"):
                continue
            if path.stem not in keep_ids:
                path.unlink(missing_ok=True)
        self._write_index(keep)

    async def delete_run(self, run_id: str) -> bool:
        async with self._lock:
            path = self._run_path(run_id)
            existed = path.exists()
            path.unlink(missing_ok=True)
            if existed:
                runs = [entry for entry in self._read_index() if entry.run_id != run_id]
                self._write_index(runs)
            return existed
