"""Run: python -m tests.test_m2"""
from datetime import datetime, timedelta, timezone

from src.db import connect
from src.extract.base import Claim, Entity, keep
from src.extract.heuristic import HeuristicExtractor
from src.extract.run import run
from src.graph.build import build, evidence_chain, neighbours
from src.score.engine import components, score_all, topic_of

text = "Nvidia partners with OpenAI on a new GPU cluster. Measles cases rise in Texas."
claims = HeuristicExtractor().extract(text)
names = {c.a.name for c in claims}
assert {"Nvidia", "OpenAI", "GPU", "measles"} <= names, names
assert all(c.evidence_quote in text for c in claims)  # FR-2.3 verbatim evidence
assert any(c.label == "partners_with" for c in claims)
fake = Claim(Entity("X", "product"), Entity("X", "product"), "mentioned_in", "x", "not in the text")
assert keep([fake], text) == []  # no evidence, no signal

now = datetime(2026, 11, 18, tzinfo=timezone.utc)
d = lambda days: now - timedelta(days=days)
fresh = components([(d(1), "paper", "arxiv", "ai"), (d(0), "news", "gdelt:a.com", "health"),
                    (d(0), "forum", "hackernews", "energy")], now)
flat = components([(d(i % 14), "news", "gdelt:a.com", "ai") for i in range(20)], now)
assert fresh["novelty"] > flat["novelty"] and fresh["velocity"] > flat["velocity"]  # FR-4.3, FR-4.4
assert fresh["corroboration"] > flat["corroboration"] and fresh["weirdness"] > flat["weirdness"] == 0
assert all(0 <= v <= 100 for v in fresh.values())
assert topic_of("topic: ai\nTitle") == "ai" and topic_of('{"topic": "health"}') == "health"

con = connect(":memory:")
docs = [("gdelt:a.com", "news", "https://a.com/1", "2026-11-16T00:00:00+00:00", '{"topic": "ai"}', text),
        ("arxiv", "paper", "https://arxiv.org/abs/1", "2026-11-17T00:00:00+00:00", "topic: ai\nx", "Nvidia GPU study.")]
con.executemany("INSERT INTO documents (source, source_type, url, published_at, collected_at, raw_text, cleaned_text) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", [(s, t, u, p, p, r, c) for s, t, u, p, r, c in docs])
run(con)
nv = con.execute("SELECT id, mention_count, first_seen_at FROM entities WHERE name = 'Nvidia'").fetchone()
assert nv[1] == 2 and nv[2].startswith("2026-11-16")
chain = evidence_chain(con, nv[0])
assert [c["source_type"] for c in chain] == ["news", "paper"] and all(c["url"] and c["evidence_quote"] for c in chain)
g = build(con)
assert "OpenAI" in [g.nodes[n]["name"] for n in neighbours(g, nv[0])]
assert score_all(con, now) >= 4
assert run(con) == (0, 0)  # rerun processes nothing twice
print("ok")
