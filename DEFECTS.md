# Defect Log: Restful-Booker API

Found by the regression suite in `tests/`. Each defect has a test that describes the
correct behavior and is expected to fail. `xfail_strict` is on, so if a defect is
fixed, its test passes and the run fails. That way this log never goes stale.

| ID | Severity | Endpoint | Expected | Actual |
|---|---|---|---|---|
| DEF-001 | High | `POST /auth` | Wrong password returns **401 Unauthorized** | Returns **200 OK** with `{"reason": "Bad credentials"}` |
| DEF-002 | High | `POST /booking` | Missing required fields returns **400** with a message | Server crashes: **500 Internal Server Error** |
| DEF-006 | High | `POST /booking` | Non-numeric `totalprice` is rejected with **400** | Accepted, and the price is **silently saved as `null`** |
| DEF-007 | High | `POST /booking` | Invalid check-in date is rejected with **400** | Accepted, and the date is **saved as `"0NaN-aN-aN"`** |
| DEF-003 | Medium | `POST /booking` | Checkout before check-in is rejected with **400** | Accepted and saved (**200**) |
| DEF-004 | Medium | `POST /booking` | Negative `totalprice` is rejected with **400** | Accepted and saved (**200**) |
| DEF-008 | Medium | `POST /booking` | Empty `firstname` is rejected with **400** | Accepted and saved (**200**) |
| DEF-009 | Low | `POST /booking` | Non-boolean `depositpaid` (`"yes"`) is rejected with **400** | Silently converted to `true` and saved |
| DEF-005 | Low | `DELETE /booking/{id}` | Successful delete returns **200** or **204** | Returns **201 Created** |

## Details

**DEF-001: Bad credentials report success.**
A client that checks the status code, which is the normal pattern, will treat a failed
login as a successful one. It has to parse the body to learn that it failed.
Steps: `POST /auth` with `{"username": "admin", "password": "wrong"}`.

**DEF-002: Incomplete booking crashes the server.**
A 500 hides the real problem from the caller and points to unhandled input on the
server. Steps: `POST /booking` with `{"firstname": "OnlyAFirstName"}`.

**DEF-006 and DEF-007: Bad values are corrupted instead of rejected.**
These are the most serious data problems. The API reports success, but the stored
record is not what was sent: a price of `"abc"` becomes `null`, and a date of
`"not-a-date"` becomes `"0NaN-aN-aN"`. The caller has no way to know the data is bad
until someone reads it back.

**DEF-003, DEF-004, DEF-008: Impossible values accepted.**
A stay that ends before it starts, a negative price, and a booking with no first
name are all saved as if valid.

**DEF-009: Silent type conversion.**
`"depositpaid": "yes"` is stored as `true`. It happens to match the intent here, but
any non-empty string, including `"no"`, would likely be converted the same way.

**DEF-005: Wrong success code on delete.**
201 means "created". Clients that check for 200 or 204 will misreport the result.
