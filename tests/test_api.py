
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_local_fix_schema():
    payload = {"language": "python", "cwe": "CWE-89", "code": "print('hi')"}
    r = client.post("/local_fix", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert "fixed_code" in j
    assert "diff" in j
    assert "explanation" in j
    assert "model_used" in j
    assert "token_usage" in j
    assert "latency_ms" in j

