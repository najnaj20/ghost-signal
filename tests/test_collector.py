"""Run: python -m tests.test_collector"""
from src.collector.gdelt import store, to_iso, to_row
from src.db import connect

a = {"url": "https://example.org/x", "title": " Hello  world ", "seendate": "20261118T093000Z",
     "domain": "example.org", "language": "English"}
con = connect(":memory:")
row = to_row(a, "ai", "2026-11-18T10:00:00+00:00")
assert row["title"] == "Hello world" and row["published_at"] == "2026-11-18T09:30:00+00:00"
assert to_row({**a, "language": "French"}, "ai", "t") is None
assert store(con, [row]) == 1 and store(con, [row]) == 0  # FR-1.4 dedup by URL
assert to_iso("20260101T000000Z").startswith("2026-01-01T00:00:00")
print("ok")
