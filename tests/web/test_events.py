from __future__ import annotations

import threading
import time

from tests.web.conftest import (
    BlockingBackend,
    RaisingBackend,
    build_client,
    collect_sse,
    shipped_extraction,
    shipped_verification,
    wait_for_terminal,
)


def test_completed_run_replays_full_event_stream(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]
        wait_for_terminal(client, run_id)

        frames = collect_sse(client, run_id)

        assert [index for index, _ in frames] == [0, 1, 2, 3]
        assert [event["stage"] for _, event in frames] == [
            "started",
            "extracting",
            "verifying",
            "delivered",
        ]


def test_after_resumes_from_index(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]
        wait_for_terminal(client, run_id)

        frames = collect_sse(client, run_id, after=2)

        assert [index for index, _ in frames] == [2, 3]
        assert [event["stage"] for _, event in frames] == ["verifying", "delivered"]


def test_live_stream_joining_mid_run_replays_without_duplicates(tmp_path) -> None:
    blocking = BlockingBackend(
        extractions=[shipped_extraction()], verifications=[shipped_verification()]
    )
    client, backend = build_client(tmp_path, backend=blocking)
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]

        # Wait until started+extracting have been published (extract blocks afterwards),
        # then connect: the stream must not re-deliver events already in the replay.
        deadline = time.monotonic() + 5.0
        while backend.extract_calls == 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert backend.extract_calls == 1

        result: dict = {}
        consumer = threading.Thread(
            target=lambda: result.update(frames=collect_sse(client, run_id)),
            daemon=True,
        )
        consumer.start()
        time.sleep(0.2)

        client.portal.call(blocking.release.set)
        consumer.join(timeout=5.0)
        assert not consumer.is_alive()

        stages = [event["stage"] for _, event in result["frames"]]
        assert stages == ["started", "extracting", "verifying", "delivered"]


def test_live_stream_carries_events_until_terminal(tmp_path) -> None:
    blocking = BlockingBackend(
        extractions=[shipped_extraction()], verifications=[shipped_verification()]
    )
    client, backend = build_client(tmp_path, backend=blocking)
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]

        result: dict = {}
        consumer = threading.Thread(
            target=lambda: result.update(frames=collect_sse(client, run_id)),
            daemon=True,
        )
        consumer.start()

        deadline = time.monotonic() + 5.0
        while backend.extract_calls == 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert backend.extract_calls == 1

        client.portal.call(blocking.release.set)
        consumer.join(timeout=5.0)
        assert not consumer.is_alive()

        stages = [event["stage"] for _, event in result["frames"]]
        assert stages == ["started", "extracting", "verifying", "delivered"]


def test_failed_run_streams_failed_terminal(tmp_path) -> None:
    client, _ = build_client(tmp_path, backend=RaisingBackend(extractions=[], verifications=[]))
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]

        detail = wait_for_terminal(client, run_id)
        assert detail["status"] == "failed"
        assert "simulated outage" in detail["error"]

        frames = collect_sse(client, run_id)
        assert frames[-1][1]["stage"] == "failed"
        assert "simulated outage" in frames[-1][1]["message"]


def test_unknown_run_events_is_404(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        assert client.get("/api/runs/" + "0" * 32 + "/events").status_code == 404
