from __future__ import annotations

from fastapi.testclient import TestClient

from xautomation.api.app import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
