# Structure steering

- src/db.py: connection and schema.
- src/collector/: one module per source, run.py entry point.
- tests/: plain assert scripts, run with python -m tests.<name>.
- data/ is gitignored.
