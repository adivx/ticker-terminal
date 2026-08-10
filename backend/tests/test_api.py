"""API-level tests for the FastAPI app.

Hermetic: app.main is imported with TERMINAL_DB pointed at a temp dir so no
repo-local database file is touched.
"""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    os.environ["TERMINAL_DB"] = str(tmp_path_factory.mktemp("db") / "terminal.db")
    from app.main import app

    return TestClient(app)


def test_mon_is_clean_400_not_500(client):
    # MON <GO> parses as a special command but dispatch has no handler for it
    # yet. It must come back as a 400 user error, never a 500 traceback.
    resp = client.get("/api/function", params={"cmd": "MON <GO>"})
    assert resp.status_code == 400
    assert "Unhandled function MON" in resp.text


def test_help_returns_reference(client):
    resp = client.get("/api/function", params={"cmd": "HELP <GO>"})
    assert resp.status_code == 200
    assert resp.json()["screen"]["type"] == "help"


def test_parse_error_is_400(client):
    # A function code that is not in FUNCTIONS is caught at parse time.
    resp = client.get("/api/function", params={"cmd": "AAPL US Equity BOGUS <GO>"})
    assert resp.status_code == 400
    assert "Unknown function code" in resp.text
