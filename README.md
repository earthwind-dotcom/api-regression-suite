# API Regression Suite

An automated regression suite for [Restful-Booker](https://restful-booker.herokuapp.com/apidoc/index.html),
a public hotel-booking API built for testers to practice on. Written in Python with
`pytest` and `requests`.

## What it covers

- **Health and authentication:** the service is up, valid logins return a token, bad logins are rejected
- **Create, read, update, delete:** every booking operation, each checked by reading the data back
- **Access control:** updates and deletes without a token are refused and change nothing
- **Negative tests:** missing fields, impossible dates, and negative prices

Each test creates its own booking with a unique name and deletes it afterwards, so
runs are independent and don't collide with other people using the shared API.

## Results

**16 tests: 11 pass, and 5 document real defects.** See [DEFECTS.md](DEFECTS.md).

Known defects are marked `xfail(strict=True)`. A defect test is *expected* to fail.
If the API is ever fixed, that test passes and strict mode fails the run, so the
defect log can't quietly go out of date.

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -rxX
```

Point it at another copy of the API with `BOOKER_URL=https://... .venv/bin/pytest`.
