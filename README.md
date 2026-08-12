# TC Fulfilment API — Defective Starter Project

This repository contains an existing Flask and SQLite service. It starts and its basic smoke tests pass, but its behaviour is not production-safe. Read `PROBLEM_STATEMENT.md` before changing the code.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Run tests:

```bash
pytest -q
```

The service creates and seeds its SQLite database automatically. Available stock:

| SKU | Initial quantity |
|---|---:|
| `SKU-KEYBOARD` | 5 |
| `SKU-MOUSE` | 10 |
| `SKU-HEADSET` | 3 |

Use `sample_requests.http`, Postman, Insomnia, or `curl` to exercise the API.

## Important

The supplied tests are only smoke tests and do not prove that the application is correct. You are expected to find defects, implement the stated contract, and add a meaningful automated test suite.
