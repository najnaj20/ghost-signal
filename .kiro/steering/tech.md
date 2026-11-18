# Tech steering

- Python 3.11, standard library first. SQLite at data/ghost-signal.db.
- Schema is fixed by PRD.md section 7. Do not add or rename columns.
- Zero budget: no paid keys, no sign-ups. GDELT DOC 2.0 API is the M1 source.
- GDELT rate limit: at most one request every 5 seconds; back off on HTTP 429.
- No em dashes in code comments or docs.
