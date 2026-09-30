"""Regression suite for the Restful-Booker API.

Tests marked with `KNOWN_DEFECT` describe the behavior the API *should* have.
They are expected to fail. `xfail_strict` is on (see pytest.ini), so if a defect
is ever fixed the test passes, the run fails, and we know to update DEFECTS.md.
"""

import pytest

from conftest import assert_booking_shape, auth


def known_defect(defect_id):
    return pytest.mark.xfail(reason=f"{defect_id}, see DEFECTS.md")


# --- Health and authentication -------------------------------------------------

@pytest.mark.smoke
def test_ping_is_up(api):
    assert api.get("/ping").status_code == 201


@pytest.mark.smoke
@pytest.mark.security
def test_auth_valid_credentials_returns_token(api, token):
    assert isinstance(token, str) and token


@pytest.mark.security
@known_defect("DEF-001")
def test_auth_bad_credentials_returns_401(api):
    resp = api.post("/auth", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


# --- Create and read -----------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.crud
def test_create_booking_returns_what_was_sent(create_booking, booking_payload):
    resp = create_booking(booking_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["bookingid"], int)
    assert body["booking"] == booking_payload
    assert_booking_shape(body["booking"])


@pytest.mark.crud
def test_get_booking_matches_created_data(api, booking):
    booking_id, payload = booking
    resp = api.get(f"/booking/{booking_id}")
    assert resp.status_code == 200
    assert resp.json() == payload
    assert_booking_shape(resp.json())


@pytest.mark.crud
def test_new_booking_appears_in_name_filter(api, booking):
    booking_id, payload = booking
    resp = api.get(
        "/booking",
        params={"firstname": payload["firstname"], "lastname": payload["lastname"]},
    )
    assert resp.status_code == 200
    assert {"bookingid": booking_id} in resp.json()


@pytest.mark.crud
def test_new_booking_appears_in_date_filter(api, booking):
    booking_id, _ = booking
    resp = api.get("/booking", params={"checkin": "2027-01-09", "checkout": "2027-01-15"})
    assert resp.status_code == 200
    assert {"bookingid": booking_id} in resp.json()


@pytest.mark.crud
def test_get_missing_booking_returns_404(api):
    assert api.get("/booking/999999999").status_code == 404


# --- Update and delete ---------------------------------------------------------

@pytest.mark.crud
def test_full_update_replaces_booking(api, token, booking):
    booking_id, payload = booking
    updated = {**payload, "totalprice": 275, "additionalneeds": "Late checkout"}
    resp = api.put(f"/booking/{booking_id}", json=updated, headers=auth(token))
    assert resp.status_code == 200
    assert api.get(f"/booking/{booking_id}").json() == updated


@pytest.mark.crud
def test_partial_update_changes_only_given_fields(api, token, booking):
    booking_id, payload = booking
    resp = api.patch(f"/booking/{booking_id}", json={"firstname": "Changed"}, headers=auth(token))
    assert resp.status_code == 200
    assert api.get(f"/booking/{booking_id}").json() == {**payload, "firstname": "Changed"}


@pytest.mark.crud
def test_deleted_booking_is_gone(api, token, booking):
    booking_id, _ = booking
    api.delete(f"/booking/{booking_id}", headers=auth(token))
    assert api.get(f"/booking/{booking_id}").status_code == 404


@pytest.mark.crud
@known_defect("DEF-005")
def test_delete_returns_200_or_204(api, token, booking):
    booking_id, _ = booking
    resp = api.delete(f"/booking/{booking_id}", headers=auth(token))
    assert resp.status_code in (200, 204)


# --- Access control: changes without a valid token are refused ------------------

@pytest.mark.security
@pytest.mark.parametrize(
    "method, headers",
    [
        pytest.param("put", {}, id="PUT-no-token"),
        pytest.param("put", {"Cookie": "token=not-a-real-token"}, id="PUT-invalid-token"),
        pytest.param("patch", {}, id="PATCH-no-token"),
        pytest.param("delete", {}, id="DELETE-no-token"),
    ],
)
def test_changes_without_valid_token_are_refused(api, booking, method, headers):
    booking_id, payload = booking
    kwargs = {"headers": headers}
    if method != "delete":
        kwargs["json"] = {**payload, "firstname": "Hacked"}
    resp = getattr(api, method)(f"/booking/{booking_id}", **kwargs)
    assert resp.status_code == 403
    assert api.get(f"/booking/{booking_id}").json() == payload  # nothing changed


# --- Negative tests: bad input should be rejected with 400 ----------------------

def _bad(payload, **changes):
    return {**payload, **changes}


NEGATIVE_CASES = [
    pytest.param(
        lambda p: {"firstname": "OnlyAFirstName"},
        id="missing-required-fields", marks=known_defect("DEF-002"),
    ),
    pytest.param(
        lambda p: _bad(p, bookingdates={"checkin": "2027-01-14", "checkout": "2027-01-10"}),
        id="checkout-before-checkin", marks=known_defect("DEF-003"),
    ),
    pytest.param(
        lambda p: _bad(p, totalprice=-100),
        id="negative-price", marks=known_defect("DEF-004"),
    ),
    pytest.param(
        lambda p: _bad(p, totalprice="abc"),
        id="price-not-a-number", marks=known_defect("DEF-006"),
    ),
    pytest.param(
        lambda p: _bad(p, bookingdates={"checkin": "not-a-date", "checkout": "2027-01-12"}),
        id="checkin-not-a-date", marks=known_defect("DEF-007"),
    ),
    pytest.param(
        lambda p: _bad(p, firstname=""),
        id="empty-firstname", marks=known_defect("DEF-008"),
    ),
    pytest.param(
        lambda p: _bad(p, depositpaid="yes"),
        id="deposit-not-a-boolean", marks=known_defect("DEF-009"),
    ),
]


@pytest.mark.negative
@pytest.mark.parametrize("make_payload", NEGATIVE_CASES)
def test_invalid_booking_is_rejected(create_booking, booking_payload, make_payload):
    resp = create_booking(make_payload(booking_payload))
    assert resp.status_code == 400
