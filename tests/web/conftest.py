from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from minuteflow.config import Settings
from minuteflow.exceptions import AgentRuntimeError
from minuteflow.schemas import (
    CandidateReview,
    DecisionCandidate,
    EvidenceSpan,
    ExtractionOutput,
    VerificationOutput,
)
from minuteflow.web.app import create_app
from tests.helpers import ScriptedBackend


def shipped_extraction() -> ExtractionOutput:
    return ExtractionOutput(
        summary="A release decision was made.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Ship on Friday.",
                classification="confirmed_decision",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )


def shipped_verification() -> VerificationOutput:
    return VerificationOutput(
        reviews=[CandidateReview(candidate_id="D1", verdict="pass", reason="Direct evidence.")]
    )


class BlockingBackend(ScriptedBackend):
    """Extraction blocks until released, holding a run in the running state."""

    def __init__(
        self, extractions: list[ExtractionOutput], verifications: list[VerificationOutput]
    ) -> None:
        super().__init__(extractions=extractions, verifications=verifications)
        self.release = asyncio.Event()
        self.started = asyncio.Event()

    async def extract(self, document, *, feedback=None):
        self.extract_calls += 1
        self.feedback_received.append(feedback)
        self.started.set()
        await self.release.wait()
        return self.extractions.pop(0)


class RaisingBackend(ScriptedBackend):
    """Extraction raises AgentRuntimeError, exercising the failed-run path."""

    async def extract(self, document, *, feedback=None):
        del document, feedback
        raise AgentRuntimeError("Extraction Agent failed: simulated outage")


def build_client(
    tmp_path: Path,
    *,
    backend: ScriptedBackend | None = None,
    settings: Settings | None = None,
    max_concurrent_runs: int = 2,
    history_max_runs: int = 50,
) -> tuple[TestClient, ScriptedBackend]:
    resolved = backend or ScriptedBackend(
        extractions=[shipped_extraction()], verifications=[shipped_verification()]
    )
    app = create_app(
        backend=resolved,
        settings=settings,
        history_dir=tmp_path / "history",
        max_concurrent_runs=max_concurrent_runs,
        history_max_runs=history_max_runs,
    )
    return TestClient(app), resolved


def wait_for_terminal(client: TestClient, run_id: str, *, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/runs/{run_id}")
        assert response.status_code == 200
        detail = response.json()
        if detail["status"] in ("delivered", "failed"):
            return detail
        time.sleep(0.02)
    pytest.fail(f"run {run_id} did not finish within {timeout}s")


def collect_sse(client: TestClient, run_id: str, *, after: int = 0) -> list[tuple[int, dict]]:
    """Read an event stream to completion and return (id, data) pairs."""
    frames: list[tuple[int, dict]] = []
    url = f"/api/runs/{run_id}/events?after={after}"
    with client.stream("GET", url) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        current_id: int | None = None
        for line in response.iter_lines():
            if line.startswith("id: "):
                current_id = int(line[4:])
            elif line.startswith("data: ") and current_id is not None:
                frames.append((current_id, json.loads(line[6:])))
    return frames
