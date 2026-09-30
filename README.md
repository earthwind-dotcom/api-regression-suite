# API Regression Suite

[![API regression](https://github.com/earthwind-dotcom/api-regression-suite/actions/workflows/regression.yml/badge.svg)](https://github.com/earthwind-dotcom/api-regression-suite/actions/workflows/regression.yml)

An automated regression suite for [Restful-Booker](https://restful-booker.herokuapp.com/apidoc/index.html),
a public hotel-booking API built for testers to practice on. Written in Python with
`pytest` and `requests`, and run automatically by GitHub Actions on every push and
every night.

## Results

**23 tests: 14 pass, and 9 document real defects.** See [DEFECTS.md](DEFECTS.md).
The most serious: a wrong password is reported as a successful login, and invalid
values are silently corrupted (a price of `"abc"` is saved as `null`) instead of
rejected.

## What it covers

| Group | Marker | What it checks |
|---|---|---|
| Smoke | `smoke` | The service is up, login works, a booking can be created |
| CRUD | `crud` | Create, read, update, partial update, delete, and search by name and date. Every change is checked by reading the data back |
| Security | `security` | Bad logins are rejected; updates and deletes with no token or a fake token are refused and change nothing |
| Negative | `negative` | Seven kinds of invalid input, from missing fields to wrong data types, in one table-driven test |

Responses are also checked against the documented contract: every field present, with
the right type.

## How it's built

- **Independent tests.** Each test creates its own booking with a unique name, and a
  fixture deletes everything the test created, even if the test fails. Runs don't
  depend on each other or collide with other people using the shared API.
- **Defects that can't go stale.** Known defects are `xfail` tests that describe the
  correct behavior, with `xfail_strict` on. If the API is ever fixed, the test passes,
  the run fails, and the defect log gets updated.
- **Retries that don't hide bugs.** The free host sometimes returns gateway errors, so
  safe requests (GET, PUT, DELETE) are retried on 502, 503, and 504. POST is never
  retried, so a real server error like DEF-002 is still reported.
- **Reports.** Every run writes a JUnit XML report, which CI keeps as an artifact.

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest                 # everything
.venv/bin/pytest -m smoke        # just the quick checks
.venv/bin/pytest -m "not negative"
```

Point it at another copy of the API with `BOOKER_URL=https://... .venv/bin/pytest`.
The login uses the public practice credentials from the Restful-Booker docs; override
them with `BOOKER_USER` and `BOOKER_PASSWORD`.
