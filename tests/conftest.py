"""Shared fixtures for the Restful-Booker regression suite."""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BOOKER_URL", "https://restful-booker.herokuapp.com")
TIMEOUT = 15
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


class Api:
    """Thin wrapper so every test uses the same base URL, headers, and timeout."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(JSON_HEADERS)

    def request(self, method, path, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        return self.session.request(method, f"{self.base_url}{path}", **kwargs)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)


@pytest.fixture(scope="session")
def api():
    return Api(BASE_URL)


@pytest.fixture(scope="session")
def token(api):
    resp = api.post("/auth", json={"username": "admin", "password": "password123"})
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def booking_payload():
    """A valid booking with a unique name, so tests never collide with other users' data."""
    return {
        "firstname": "QA",
        "lastname": f"Test-{uuid.uuid4().hex[:8]}",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {"checkin": "2027-01-10", "checkout": "2027-01-14"},
        "additionalneeds": "Breakfast",
    }


@pytest.fixture
def booking(api, token, booking_payload):
    """Create a booking for the test, then clean it up afterwards."""
    resp = api.post("/booking", json=booking_payload)
    assert resp.status_code == 200, resp.text
    booking_id = resp.json()["bookingid"]
    yield booking_id, booking_payload
    api.delete(f"/booking/{booking_id}", headers={"Cookie": f"token={token}"})
