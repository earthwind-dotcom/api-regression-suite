# Defect Log: Restful-Booker API

Found by the regression suite in `tests/`. Each defect has a test marked
`xfail(strict=True)` that describes the correct behavior. If the defect is fixed,
that test passes and strict mode fails the run, so this log never goes stale.

| ID | Severity | Endpoint | Expected | Actual |
|---|---|---|---|---|
| DEF-001 | High | `POST /auth` | Wrong password returns **401 Unauthorized** | Returns **200 OK** with `{"reason": "Bad credentials"}` |
| DEF-002 | High | `POST /booking` | Missing required fields returns **400** with a message | Server crashes: **500 Internal Server Error** |
| DEF-003 | Medium | `POST /booking` | Checkout before check-in is rejected with **400** | Accepted and saved (**200**) |
| DEF-004 | Medium | `POST /booking` | Negative `totalprice` is rejected with **400** | Accepted and saved (**200**) |
| DEF-005 | Low | `DELETE /booking/{id}` | Successful delete returns **200** or **204** | Returns **201 Created** |

## Details

**DEF-001: Bad credentials report success.**
Any client that checks the status code, which is the normal pattern, will treat a
failed login as a successful one. It has to parse the body to learn that it failed.
Steps: `POST /auth` with `{"username": "admin", "password": "wrong"}`.

**DEF-002: Incomplete booking crashes the server.**
A 500 hides the real problem from the caller and suggests unhandled input on the
server. Steps: `POST /booking` with `{"firstname": "OnlyAFirstName"}`.

**DEF-003: Impossible date range accepted.**
Steps: `POST /booking` with check-in `2027-01-14` and checkout `2027-01-10`.

**DEF-004: Negative price accepted.**
Steps: `POST /booking` with `"totalprice": -100`.

**DEF-005: Wrong success code on delete.**
201 means "created". Clients that check for 200 or 204 will misreport the result.
Steps: `DELETE /booking/{id}` with a valid token.
