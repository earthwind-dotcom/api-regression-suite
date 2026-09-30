"""Shared fixtures for the Restful-Booker regression suite."""

import os
import uuid

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.environ.get("BOOKER_URL", "https://restful-booker.herokuapp.com")
TIMEOUT = 15
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# Public practice credentials published in the Restful-Booker docs, not secrets.
USERNAME = os.environ.get("BOOKER_USER", "admin")
PASSWORD = os.environ.get("BOOKER_PASSWORD", "password123")

# Retry only idempotent requests on gateway errors from the shared free host.
# POST is never retried, so a real 500 from the API (see DEF-002) still shows up.
RETRY = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(502, 503, 504),
    allowed_methods=frozenset({"GET", "PUT", "DELETE", "HEAD", "OPTIONS"}),
    raise_on_status=False,
)


class Api:
    """Thin wrapper so every test uses the same base URL, headers, timeout, and retries."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(JSON_HEADERS)
        self.session.mount("https://", HTTPAdapter(max_retries=RETRY))
        self.session.mount("http://", HTTPAdapter(max_retries=RETRY))

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


def auth(token):
    return {"Cookie": f"token={token}"}


def assert_booking_shape(booking):
    """Contract check: every field is present and has the documented type."""
    assert isinstance(booking["firstname"], str)
    assert isinstance(booking["lastname"], str)
    assert isinstance(booking["totalprice"], int)
    assert isinstance(booking["depositpaid"], bool)
    assert isinstance(booking["bookingdates"]["checkin"], str)
    assert isinstance(booking["bookingdates"]["checkout"], str)


@pytest.fixture(scope="session")
def api():
    return Api(BASE_URL)


@pytest.fixture(scope="session")
def token(api):
    resp = api.post("/auth", json={"username": USERNAME, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
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
def create_booking(api, token):
    """Create bookings during a test; every one is deleted afterwards, pass or fail."""
    created = []

    def _create(payload):
        resp = api.post("/booking", json=payload)
        if resp.status_code == 200:
            created.append(resp.json()["bookingid"])
        return resp

    yield _create
    for booking_id in created:
        api.delete(f"/booking/{booking_id}", headers=auth(token))


@pytest.fixture
def booking(create_booking, booking_payload):
    """One valid booking for the test: (id, payload)."""
    resp = create_booking(booking_payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["bookingid"], booking_payload
