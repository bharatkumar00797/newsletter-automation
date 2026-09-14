# tools/

Python scripts that do the actual work: API calls, data transformations, file I/O, database queries. Deterministic and testable — no reasoning happens here.

Conventions:
- One script per discrete capability (e.g. `scrape_single_site.py`, `send_newsletter.py`).
- Read credentials from `.env` (via `python-dotenv` or similar) — never hardcode secrets.
- Write intermediates to `.tmp/`, not the project root.
- Prefer a `main()` with clear CLI args so a workflow step can call the script directly.
