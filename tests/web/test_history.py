from __future__ import annotations

import time
from pathlib import Path

from minuteflow.renderers import render_json, render_markdown
from minuteflow.schemas import MeetingActionReport
from tests.web.conftest import (
    BlockingBackend,
    RaisingBackend,
    build_client,
    shipped_extraction,
    shipped_verification,
    wait_for_terminal,
)


def _run_one(client, text: str) -> str:
    run_id = client.post("/api/runs", json={"text": text}).json()["run_id"]
    wait_for_terminal(client, run_id)
    return run_id


def test_history_persists_runs_and_lists_them(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        run_id = _run_one(client, "The team decided to ship on Friday.")
        detail = client.get(f"/api/runs/{run_id}").json()

        history_dir = Path(tmp_path) / "history"
        assert (history_dir / f"{run_id}.json").exists()
        assert (history_dir / "index.json").exists()

        listing = client.get("/api/runs").json()["runs"]
        assert [entry["run_id"] for entry in listing] == [run_id]
        assert listing[0]["status"] == "delivered"
        assert listing[0]["summary"] == detail["report"]["summary"]


def test_history_prunes_oldest_runs(tmp_path) -> None:
    client, _ = build_client(tmp_path, history_max_runs=2)
    with client:
        first = _run_one(client, "First meeting decided on a plan.")
        second = _run_one(client, "Second meeting decided on a plan.")
        third = _run_one(client, "Third meeting decided on a plan.")

        listing = client.get("/api/runs").json()["runs"]
        assert [entry["run_id"] for entry in listing] == [third, second]

        history_dir = Path(tmp_path) / "history"
        assert not (history_dir / f"{first}.json").exists()
        assert client.get(f"/api/runs/{first}").status_code == 404


def test_delete_run_removes_files_and_index_entry(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        run_id = _run_one(client, "The team decided to ship on Friday.")
        assert client.delete(f"/api/runs/{run_id}").status_code == 204
        assert client.delete(f"/api/runs/{run_id}").status_code == 404
        assert client.get(f"/api/runs/{run_id}").status_code == 404
        assert client.get("/api/runs").json()["runs"] == []


def test_delete_running_run_is_409(tmp_path) -> None:
    blocking = BlockingBackend(
        extractions=[shipped_extraction()], verifications=[shipped_verification()]
    )
    client, backend = build_client(tmp_path, backend=blocking)
    with client:
        response = client.post("/api/runs", json={"text": "The team decided to ship on Friday."})
        run_id = response.json()["run_id"]

        deadline = time.monotonic() + 5.0
        while backend.extract_calls == 0 and time.monotonic() < deadline:
            time.sleep(0.02)

        assert client.delete(f"/api/runs/{run_id}").status_code == 409

        client.portal.call(blocking.release.set)
        wait_for_terminal(client, run_id)


def test_export_matches_renderers(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        run_id = _run_one(client, "The team decided to ship on Friday.")
        report = MeetingActionReport.model_validate(
            client.get(f"/api/runs/{run_id}").json()["report"]
        )

        markdown = client.get(f"/api/runs/{run_id}/export?format=markdown")
        assert markdown.status_code == 200
        assert markdown.text == render_markdown(report)
        assert markdown.headers["content-disposition"].startswith(
            f'attachment; filename="minuteflow-{run_id}.md"'
        )

        json_export = client.get(f"/api/runs/{run_id}/export?format=json")
        assert json_export.status_code == 200
        assert json_export.text == render_json(report)
        assert json_export.headers["content-disposition"].startswith(
            f'attachment; filename="minuteflow-{run_id}.json"'
        )

        assert client.get(f"/api/runs/{run_id}/export?format=xml").status_code == 422


def test_export_unknown_or_failed_run_is_404(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        assert client.get("/api/runs/" + "0" * 32 + "/export").status_code == 404

    failing, _ = build_client(tmp_path, backend=RaisingBackend(extractions=[], verifications=[]))
    with failing:
        run_id = failing.post("/api/runs", json={"text": "x"}).json()["run_id"]
        wait_for_terminal(failing, run_id)
        assert failing.get(f"/api/runs/{run_id}/export").status_code == 404
