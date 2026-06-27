"""Shared pytest fixtures.

Everything here makes the tests run offline, fast and free:
- a throwaway SQLite database and a temporary Qdrant directory (per test session),
- a FAKE Gemini (no network calls, no API key, no cost).

Environment variables are set BEFORE importing the app, because config.py reads
them at import time.
"""

import os
import tempfile

import pytest

# ── Configure a throwaway environment before importing the app ────────────────
_TMP = tempfile.mkdtemp(prefix="pdfchat_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db")
os.environ["QDRANT_PATH"] = os.path.join(_TMP, "qdrant")
os.environ["ENVIRONMENT"] = "development"
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")

import gemini_client  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import api  # noqa: E402


# ── Fake Gemini (deterministic, no network) ──────────────────────────────────
def _fake_embed(text, task_type=None):
    # A small, deterministic vector derived from the text bytes.
    vec = [0.0] * 8
    for i, byte in enumerate(text.encode("utf-8")):
        vec[i % 8] += byte % 7 + 1
    return vec


def _fake_generate(prompt):
    return "This is a test answer based on the provided context."


@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    # Replace the real Gemini calls for every test.
    monkeypatch.setattr(gemini_client, "embed", _fake_embed)
    monkeypatch.setattr(gemini_client, "generate", _fake_generate)


@pytest.fixture
def client():
    # A TestClient context runs the app's startup (creates DB tables).
    with TestClient(api.app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    # Register + log in a user and return the Authorization header for them.
    def _make(email, password="password123"):
        client.post("/register", json={"email": email, "password": password})
        res = client.post("/login", data={"username": email, "password": password})
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def make_pdf():
    # Build a tiny in-memory PDF containing the given text (real, parseable PDF).
    import fitz

    def _make(text):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        data = doc.tobytes()
        doc.close()
        return data

    return _make
