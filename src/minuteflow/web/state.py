"""In-memory per-run state for the web server."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime

from minuteflow.agents.backend import AgentBackend
from minuteflow.config import Settings
from minuteflow.orchestration import MinuteFlowPipeline
from minuteflow.schemas import MeetingActionReport, PipelineEvent
from minuteflow.web.history import HistoryStore
from minuteflow.web.models import RunStatus


@dataclass
class RunState:
    run_id: str
    created_at: datetime
    meeting_date: date | None
    filename: str | None
    source_text: str
    status: RunStatus = "running"
    events: list[PipelineEvent] = field(default_factory=list)
    queue: asyncio.Queue[PipelineEvent | None] = field(default_factory=asyncio.Queue)
    pending_terminal: PipelineEvent | None = None
    report: MeetingActionReport | None = None
    error: str | None = None
    task: asyncio.Task[None] | None = None


@dataclass
class WebServerState:
    backend: AgentBackend
    pipeline: MinuteFlowPipeline
    settings: Settings | None
    history: HistoryStore
    max_concurrent_runs: int
    max_input_chars: int
    semaphore: asyncio.Semaphore
    active: dict[str, RunState] = field(default_factory=dict)
