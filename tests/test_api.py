import json

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_curl_conversion_success_and_redaction() -> None:
    response = client.post(
        "/api/convert/curl",
        json={
            "curl": 'curl -X POST https://api.example.com/users -H "Authorization: Bearer secret" -H "Content-Type: application/json" -d \'{"name":"Ada"}\'',
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "POST"
    assert data["body"] == {"name": "Ada"}
    assert data["headers"]["Authorization"] == "Bearer ***"
    assert "fetch" in data["code"]
    assert data["redacted"] is True


def test_curl_conversion_rejects_non_curl() -> None:
    response = client.post("/api/convert/curl", json={"curl": "https://example.com"})
    assert response.status_code == 422


def test_json_types_success() -> None:
    response = client.post(
        "/api/convert/json-types",
        json={"json": {"id": 1, "name": "Ada", "active": True}, "root_name": "User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "export interface User" in data["typescript"]
    assert data["json_schema"]["type"] == "object"
    assert data["value"]["id"] == 1


def test_json_types_rejects_invalid_json() -> None:
    response = client.post("/api/convert/json-types", json={"json": "{broken"})
    assert response.status_code == 422


def test_log_analysis_success() -> None:
    log = """2026-08-19T10:00:00Z ERROR DatabaseError: connection failed
    at db.connect(db.py:42)
2026-08-19T10:01:00Z INFO retry succeeded
"""
    response = client.post("/api/analyze/logs", json={"text": log})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["lines"] == 3
    assert data["summary"]["error_count"] == 1
    assert data["errors"][0]["exception"] == "DatabaseError"
    assert data["errors"][0]["stack"]


def test_log_analysis_requires_text() -> None:
    response = client.post("/api/analyze/logs", json={"text": ""})
    assert response.status_code == 422


def test_agent_jsonl_success_from_transcript() -> None:
    response = client.post(
        "/api/convert/agent-jsonl",
        json={"conversation": "user: What is 2+2?\nassistant: 4"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    sample = data["samples"][0]
    assert sample["input"] == "What is 2+2?"
    assert sample["expected_output"] == "4"
    assert json.loads(data["jsonl"])["id"] == "sample-001"


def test_agent_jsonl_requires_conversation_or_messages() -> None:
    response = client.post("/api/convert/agent-jsonl", json={})
    assert response.status_code == 422

