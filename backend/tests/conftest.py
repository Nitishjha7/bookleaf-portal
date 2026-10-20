import os
import tempfile

# has to be set before the app is imported
_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app import seed
from app.main import app


@pytest.fixture(scope="session")
def client():
    seed.run()
    return TestClient(app)


def login(client, email, password):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def author_h(client):
    return login(client, "priya.sharma@email.com", "author123")


@pytest.fixture(scope="session")
def admin_h(client):
    return login(client, "admin@bookleaf.com", "admin123")
