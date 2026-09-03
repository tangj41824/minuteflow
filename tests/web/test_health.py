from __future__ import annotations

from minuteflow.config import Settings
from tests.web.conftest import build_client


def test_health_reports_server_state(tmp_path) -> None:
    client, _ = build_client(tmp_path)
    with client:
        response = client.get("/api/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["version"]
        assert payload["model"] == "scripted"
        assert payload["api_key_configured"] is False
        assert payload["max_input_chars"] == 100_000
        assert payload["max_concurrent_runs"] == 2
        assert payload["history_dir"].endswith("history")


def test_health_reflects_settings(tmp_path) -> None:
    client, _ = build_client(
        tmp_path,
        settings=Settings(model="deepseek-v4-pro", api_key="sk-test", max_input_chars=1234),
        max_concurrent_runs=3,
    )
    with client:
        payload = client.get("/api/health").json()
        assert payload["model"] == "deepseek-v4-pro"
        assert payload["api_key_configured"] is True
        assert payload["max_input_chars"] == 1234
        assert payload["max_concurrent_runs"] == 3
