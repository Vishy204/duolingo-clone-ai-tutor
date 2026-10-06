import os
import tempfile

# Isolated DB and no real LLM calls for the test-suite (agents degrade to the rules engine).
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["OPENAI_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256-ok"
os.environ["DEMO_MODE"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth(client):
    r = client.post("/api/v1/auth/guest", json={}, headers={"x-forwarded-for": f"10.0.{os.urandom(1)[0]}.{os.urandom(1)[0]}"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture()
def db(client):
    from app.core.db import SessionLocal

    with SessionLocal() as s:
        yield s
