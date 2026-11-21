"""Run: python -m tests.test_m3"""
from datetime import datetime, timezone

from src.api.main import entity, feed, scores, unwatch, watch, watchlist
from src.db import connect
from src.extract.run import run
from src.score.engine import score_all

con = connect(":memory:")
docs = [("gdelt:a.com", "news", "https://a.com/1", "2026-11-17T00:00:00+00:00", "topic: health",
         "Nvidia partners with OpenAI on a new GPU cluster."),
        ("arxiv", "paper", "https://arxiv.org/abs/1", "2026-11-16T00:00:00+00:00", "topic: ai", "Nvidia GPU study.")]
con.executemany("INSERT INTO documents (source, source_type, url, published_at, collected_at, raw_text, cleaned_text) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", [(s, t, u, p, p, r, c) for s, t, u, p, r, c in docs])
run(con)
score_all(con, datetime(2026, 11, 18, tzinfo=timezone.utc))

f = feed(con)
assert [x["ghost_score"] for x in f] == sorted((x["ghost_score"] for x in f), reverse=True)  # FR-5.1
assert all(x["latest_evidence"]["evidence_quote"] and x["latest_evidence"]["url"] for x in f)  # FR-5.5
assert all(set(x["components"]) == {"novelty", "velocity", "corroboration", "weirdness"} for x in f)

nv = next(x for x in f if x["name"] == "Nvidia")
e = entity(con, nv["id"])
assert [d["source_type"] for d in e["evidence_chain"]] == ["paper", "news"]  # FR-5.2 time order
assert e["claims"] and all(c["evidence_quote"] and c["url"] for c in e["claims"])
assert entity(con, 99999) is None and scores(con, nv["id"])[0]["date"] == "2026-11-18"

assert watch(con, nv["id"]) and watch(con, nv["id"]) and not watch(con, 99999)  # idempotent, unknown id refused
assert [w["id"] for w in watchlist(con)] == [nv["id"]]
assert unwatch(con, nv["id"]) and not unwatch(con, nv["id"]) and watchlist(con) == []
print("ok")
