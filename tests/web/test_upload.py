from __future__ import annotations

from minuteflow.config import Settings
from tests.web.conftest import build_client, wait_for_terminal


def test_upload_runs_pipeline(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.post(
            "/api/runs/upload",
            files={"file": ("meeting.md", b"The team decided to ship on Friday.", "text/markdown")},
            data={"meeting_date": "2026-09-04"},
        )
        assert response.status_code == 202
        detail = wait_for_terminal(client, response.json()["run_id"])
        assert detail["status"] == "delivered"
        assert detail["meeting_date"] == "2026-09-04"
        assert detail["report"]["decisions"][0]["statement"] == "Ship on Friday."


def test_upload_missing_file_is_422(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        assert client.post("/api/runs/upload").status_code == 422


def test_upload_oversized_file_is_413(tmp_path) -> None:
    client, _ = build_client(tmp_path, settings=Settings(max_input_chars=10))
    with client:
        response = client.post(
            "/api/runs/upload",
            files={"file": ("big.md", b"x" * 11, "text/plain")},
        )
        assert response.status_code == 413


def test_upload_undecodable_bytes_is_400(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.post(
            "/api/runs/upload",
            files={"file": ("binary.md", b"\xff\xfe\x00\x01", "text/plain")},
        )
        assert response.status_code == 400
