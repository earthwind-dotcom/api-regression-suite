"""Regression suite for the Restful-Booker API.

Tests marked `xfail(strict=True)` document a known defect: they describe the
behavior the API *should* have. If a defect is ever fixed, the test starts
passing, strict mode turns that into a failure, and we know to update the
defect log (DEFECTS.md) and remove the marker.
"""

import pytest

KNOWN_DEFECT = pytest.mark.xfail(strict=True, reason="Known defect, see DEFECTS.md")


def auth(token):
    return {"Cookie": f"token={token}"}


# --- Health and authentication -------------------------------------------------

def test_ping_is_up(api):
    assert api.get("/ping").status_code == 201


def test_auth_valid_credentials_returns_token(api):
    resp = api.post("/auth", json={"username": "admin", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json().get("token")


@KNOWN_DEFECT
def test_auth_bad_credentials_returns_401(api):
    # DEF-001: bad credentials come back as 200 OK with a "reason" field.
    resp = api.post("/auth", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


# --- Create and read -----------------------------------------------------------

def test_create_booking_returns_what_was_sent(api, booking_payload):
    resp = api.post("/booking", json=booking_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["bookingid"], int)
    assert body["booking"] == booking_payload


def test_get_booking_matches_created_data(api, booking):
    booking_id, payload = booking
    resp = api.get(f"/booking/{booking_id}")
    assert resp.status_code == 200
    assert resp.json() == payload


def test_new_booking_appears_in_name_filter(api, booking):
    booking_id, payload = booking
    resp = api.get(
        "/booking",
        params={"firstname": payload["firstname"], "lastname": payload["lastname"]},
    )
    assert resp.status_code == 200
    assert {"bookingid": booking_id} in resp.json()


def test_get_missing_booking_returns_404(api):
    assert api.get("/booking/999999999").status_code == 404


# --- Update and delete ---------------------------------------------------------

def test_full_update_replaces_booking(api, token, booking):
    booking_id, payload = booking
    updated = {**payload, "totalprice": 275, "additionalneeds": "Late checkout"}
    resp = api.put(f"/booking/{booking_id}", json=updated, headers=auth(token))
    assert resp.status_code == 200
    assert api.get(f"/booking/{booking_id}").json() == updated


def test_partial_update_changes_only_given_fields(api, token, booking):
    booking_id, payload = booking
    resp = api.patch(f"/booking/{booking_id}", json={"firstname": "Changed"}, headers=auth(token))
    assert resp.status_code == 200
    assert api.get(f"/booking/{booking_id}").json() == {**payload, "firstname": "Changed"}


def test_update_without_token_is_rejected(api, booking):
    booking_id, payload = booking
    resp = api.put(f"/booking/{booking_id}", json=payload)
    assert resp.status_code == 403
    assert api.get(f"/booking/{booking_id}").json() == payload  # nothing changed


def test_delete_without_token_is_rejected(api, booking):
    booking_id, _ = booking
    assert api.delete(f"/booking/{booking_id}").status_code == 403
    assert api.get(f"/booking/{booking_id}").status_code == 200  # still there


def test_deleted_booking_is_gone(api, token, booking_payload):
    booking_id = api.post("/booking", json=booking_payload).json()["bookingid"]
    api.delete(f"/booking/{booking_id}", headers=auth(token))
    assert api.get(f"/booking/{booking_id}").status_code == 404


# --- Negative tests: bad input should be rejected cleanly -----------------------

@KNOWN_DEFECT
def test_missing_required_fields_returns_400(api):
    # DEF-002: the server crashes with 500 instead of a 400 validation error.
    resp = api.post("/booking", json={"firstname": "OnlyAFirstName"})
    assert resp.status_code == 400


@KNOWN_DEFECT
def test_checkout_before_checkin_is_rejected(api, token, booking_payload):
    # DEF-003: a stay that ends before it starts is accepted.
    bad = {**booking_payload, "bookingdates": {"checkin": "2027-01-14", "checkout": "2027-01-10"}}
    resp = api.post("/booking", json=bad)
    if resp.status_code == 200:
        api.delete(f"/booking/{resp.json()['bookingid']}", headers=auth(token))
    assert resp.status_code == 400


@KNOWN_DEFECT
def test_negative_price_is_rejected(api, token, booking_payload):
    # DEF-004: a negative total price is accepted.
    resp = api.post("/booking", json={**booking_payload, "totalprice": -100})
    if resp.status_code == 200:
        api.delete(f"/booking/{resp.json()['bookingid']}", headers=auth(token))
    assert resp.status_code == 400


@KNOWN_DEFECT
def test_delete_returns_204_or_200(api, token, booking_payload):
    # DEF-005: a successful delete returns 201 Created.
    booking_id = api.post("/booking", json=booking_payload).json()["bookingid"]
    resp = api.delete(f"/booking/{booking_id}", headers=auth(token))
    assert resp.status_code in (200, 204)
