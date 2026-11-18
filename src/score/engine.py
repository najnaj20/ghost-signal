"""Ghost Score engine (FR-4). Every component is 0 to 100; weights are fixed by PRD FR-4.2."""
import json
import math
from datetime import datetime, timedelta, timezone

WEIGHTS = {"novelty": 0.4, "velocity": 0.3, "corroboration": 0.2, "weirdness": 0.1}
SOURCE_TYPES = 3  # news, paper, forum in v1


def topic_of(raw_text):
    """Collector topic (ai / energy / health), stored in raw_text by every collector."""
    if raw_text.startswith("topic: "):
        return raw_text[7:].split("\n", 1)[0]
    try:
        return json.loads(raw_text).get("topic")
    except (ValueError, AttributeError):
        return None


def components(mentions, now):
    """mentions: list of (published_at datetime, source_type, source, topic), one per document."""
    first = min(m[0] for m in mentions)
    n = len(mentions)
    age_days = max(0.0, (now - first).total_seconds() / 86400)
    # Novelty: new this week and rarely mentioned. 1 mention: 1.0, 20: about 0.43, 1000: 0.25.
    novelty = 100 * max(0.0, 1 - age_days / 30) * (1 / (1 + math.log10(n)))
    # Velocity: share of mentions in the last 7 days, damped until there are 3 of them.
    week = now - timedelta(days=7)
    recent = sum(1 for m in mentions if m[0] >= week)
    prior = sum(1 for m in mentions if week - timedelta(days=7) <= m[0] < week)
    velocity = 100 * (recent / (recent + prior) if recent + prior else 0) * min(1.0, recent / 3)
    # Corroboration: different source types weigh most, distinct outlets add the rest.
    types, outlets = {m[1] for m in mentions}, {m[2] for m in mentions}
    corroboration = 100 * (0.7 * len(types) / SOURCE_TYPES + 0.3 * min(len(outlets), 5) / 5)
    # Weirdness: spread across topics. All in one topic: 0. Even split over three topics: 100.
    topics = [m[3] for m in mentions if m[3]]
    top = max((topics.count(t) for t in set(topics)), default=0)
    weirdness = 100 * min(1.0, 1.5 * (1 - top / len(topics))) if topics else 0.0
    c = {"novelty": novelty, "velocity": velocity, "corroboration": corroboration, "weirdness": weirdness}
    c = {k: round(v, 1) for k, v in c.items()}
    c["ghost_score"] = round(sum(c[k] * w for k, w in WEIGHTS.items()), 1)
    return c


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def score_all(con, now=None):
    now = now or datetime.now(timezone.utc)
    rows = con.execute("""SELECT r.entity_a_id, COALESCE(d.published_at, d.collected_at), d.source_type, d.source,
                          d.raw_text FROM relations r JOIN documents d ON d.id = r.doc_id
                          WHERE r.entity_a_id = r.entity_b_id GROUP BY r.entity_a_id, d.id""").fetchall()
    by_entity = {}
    for eid, ts, st, src, raw in rows:
        by_entity.setdefault(eid, []).append((parse(ts), st, src, topic_of(raw or "")))
    day = now.date().isoformat()
    for eid, ms in by_entity.items():
        c = components(ms, now)
        con.execute("INSERT OR REPLACE INTO scores VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (eid, day, c["novelty"], c["velocity"], c["corroboration"], c["weirdness"], c["ghost_score"]))
    con.commit()
    return len(by_entity)
