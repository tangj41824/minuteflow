"""HTTP API contracts for the local web app."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from minuteflow.schemas import MeetingActionReport, PipelineEvent, StrictModel

RunStatus = Literal["running", "delivered", "failed"]


class RunCreateRequest(StrictModel):
    text: str
    meeting_date: date | None = None
    filename: str | None = None


class RunSummary(StrictModel):
    run_id: str
    created_at: datetime
    status: RunStatus
    meeting_date: date | None
    summary: str | None = None
    retry_count: int | None = None
    error: str | None = None


class RunDetail(StrictModel):
    run_id: str
    created_at: datetime
    status: RunStatus
    meeting_date: date | None
    source_text: str | None = None
    events: list[PipelineEvent]
    report: MeetingActionReport | None = None
    error: str | None = None


class HealthResponse(StrictModel):
    status: Literal["ok"]
    version: str
    model: str
    api_key_configured: bool
    max_input_chars: int
    max_concurrent_runs: int
    history_dir: str
