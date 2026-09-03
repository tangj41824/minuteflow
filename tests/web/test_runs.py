from __future__ import annotations

import time

from tests.web.conftest import (
    BlockingBackend,
    build_client,
    shipped_extraction,
    shipped_verification,
    wait_for_terminal,
)


def test_create_run_delivers_report(tmp_path) -> None:
    client, backend = build_client(tmp_path)
    with client:
        response = client.post(
            "/api/runs",
            json={
                "text": "The team decided to ship on Friday.",
                "meeting_date": "2026-09-04",
                "filename": "notes.md",
            },
        )
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        assert len(run_id) == 32

        detail = wait_for_terminal(client, run_id)

        assert detail["status"] == "delivered"
        assert detail["meeting_date"] == "2026-09-04"
        assert detail["source_text"] == "The team decided to ship on Friday."
        assert detail["report"]["decisions"][0]["statement"] == "Ship on Friday."
        assert [event["stage"] for event in detail["events"]] == [
            "started",
            "extracting",
            "verifying",
            "delivered",
        ]
        assert backend.extract_calls == backend.verify_calls == 1


def test_empty_text_delivers_intake_error_without_model_call(tmp_path) -> None:
    client, backend = build_client(tmp_path)
    with client:
        response = client.post("/api/runs", json={"text": " \n"})
        run_id = response.json()["run_id"]

        detail = wait_for_terminal(client, run_id)

        assert detail["status"] == "delivered"
        assert detail["report"]["errors"] == ["The meeting notes are empty."]
        assert detail["report"]["decisions"] == []
        assert backend.extract_calls == backend.verify_calls == 0


def test_missing_text_is_422(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        assert client.post("/api/runs", json={}).status_code == 422


def test_bad_meeting_date_is_422(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.post("/api/runs", json={"text": "x", "meeting_date": "not-a-date"})
        assert response.status_code == 422


def test_second_run_returns_429_at_capacity(tmp_path) -> None:
    blocking = BlockingBackend(
        extractions=[shipped_extraction()], verifications=[shipped_verification()]
    )
    client, backend = build_client(tmp_path, backend=blocking, max_concurrent_runs=1)
    with client:
        first = client.post("/api/runs", json={"text": "Blocked on purpose."})
        assert first.status_code == 202
        first_id = first.json()["run_id"]

        deadline = time.monotonic() + 5.0
        while backend.extract_calls == 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert backend.extract_calls == 1

        second = client.post("/api/runs", json={"text": "Should be rejected."})
        assert second.status_code == 429

        client.portal.call(blocking.release.set)
        assert wait_for_terminal(client, first_id)["status"] == "delivered"

        third = client.post("/api/runs", json={"text": "Now there is capacity."})
        assert third.status_code == 202


def test_unknown_run_is_404(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        assert client.get("/api/runs/" + "0" * 32).status_code == 404
        assert client.get("/api/runs/not-a-run-id").status_code == 422
