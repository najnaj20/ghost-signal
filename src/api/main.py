"""FastAPI API (FR-5). Run: uvicorn src.api.main:app --reload

Evidence rule (PRD section 8): every claim is returned with its evidence_quote and url.
Entities without at least one evidence-backed document are never returned.
"""
from contextlib import closing
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.db import connect
from src.graph.build import evidence_chain

COMPONENTS = ("novelty", "velocity", "corroboration", "weirdness")

# Latest score row per entity, plus its newest evidence so a feed item never stands without proof.
FEED_SQL = """SELECT e.id, e.name, e.type, e.first_seen_at, e.mention_count, s.date,
       s.novelty, s.velocity, s.corroboration, s.weirdness, s.ghost_score,
       (SELECT r.evidence_quote FROM relations r JOIN documents d ON d.id = r.doc_id
        WHERE r.entity_a_id = e.id AND r.entity_b_id = e.id
        ORDER BY COALESCE(d.published_at, d.collected_at) DESC, d.id DESC LIMIT 1),
       (SELECT d.url FROM relations r JOIN documents d ON d.id = r.doc_id
        WHERE r.entity_a_id = e.id AND r.entity_b_id = e.id
        ORDER BY COALESCE(d.published_at, d.collected_at) DESC, d.id DESC LIMIT 1)
FROM entities e JOIN scores s ON s.entity_id = e.id
WHERE s.date = (SELECT MAX(date) FROM scores WHERE entity_id = e.id)"""

CLAIMS_SQL = """SELECT r.id, ea.name, eb.name, r.relation_label, r.claim_text, r.evidence_quote,
       d.url, d.source_type, COALESCE(d.published_at, d.collected_at)
FROM relations r JOIN documents d ON d.id = r.doc_id
JOIN entities ea ON ea.id = r.entity_a_id JOIN entities eb ON eb.id = r.entity_b_id
WHERE r.entity_a_id != r.entity_b_id AND (r.entity_a_id = ? OR r.entity_b_id = ?) ORDER BY 9, 1"""


def _item(row):
    eid, name, typ, first, n, day, *comp, score, quote, url = row
    return {"id": eid, "name": name, "type": typ, "first_seen_at": first, "mention_count": n,
            "score_date": day, "ghost_score": score, "components": dict(zip(COMPONENTS, comp)),
            "label": "Rising from the grave" if score > 70 else None,
            "latest_evidence": {"evidence_quote": quote, "url": url}}


def feed(con, limit=50, where="", args=()):
    rows = con.execute(f"{FEED_SQL} {where} ORDER BY s.ghost_score DESC, e.id LIMIT ?", (*args, limit))
    return [_item(r) for r in rows if r[-2] and r[-1]]  # no evidence, no signal


def entity(con, eid):
    found = feed(con, 1, "AND e.id = ?", (eid,))
    if not found:
        return None
    keys = ("relation_id", "entity_a", "entity_b", "relation_label", "claim_text", "evidence_quote", "url",
            "source_type", "published_at")
    claims = [dict(zip(keys, r)) for r in con.execute(CLAIMS_SQL, (eid, eid))]
    return {**found[0], "evidence_chain": evidence_chain(con, eid), "claims": claims}


def scores(con, eid):
    rows = con.execute("SELECT date, novelty, velocity, corroboration, weirdness, ghost_score FROM scores "
                       "WHERE entity_id = ? ORDER BY date", (eid,))
    return [{"date": d, "ghost_score": g, "components": dict(zip(COMPONENTS, c))} for d, *c, g in rows]


def watchlist(con):
    return feed(con, 1000, "AND e.id IN (SELECT entity_id FROM watchlist)")


def watch(con, eid):
    if not con.execute("SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
        return False
    con.execute("INSERT OR IGNORE INTO watchlist VALUES (?, ?)", (eid, datetime.now(timezone.utc).isoformat()))
    con.commit()
    return True


def unwatch(con, eid):
    n = con.execute("DELETE FROM watchlist WHERE entity_id = ?", (eid,)).rowcount
    con.commit()
    return n > 0


app = FastAPI(title="Ghost Signal API")


class WatchIn(BaseModel):
    entity_id: int


def _404(x, what="entity"):
    if not x:
        raise HTTPException(404, f"{what} not found")
    return x


@app.get("/feed")
def get_feed(limit: int = 50):
    with closing(connect()) as con:
        return feed(con, max(1, min(limit, 500)))


@app.get("/entities/{eid}")
def get_entity(eid: int):
    with closing(connect()) as con:
        return _404(entity(con, eid))


@app.get("/entities/{eid}/scores")
def get_scores(eid: int):
    with closing(connect()) as con:
        return _404(scores(con, eid))


@app.get("/watchlist")
def get_watchlist():
    with closing(connect()) as con:
        return watchlist(con)


@app.post("/watchlist", status_code=201)
def post_watchlist(body: WatchIn):
    with closing(connect()) as con:
        _404(watch(con, body.entity_id))
        return {"entity_id": body.entity_id}


@app.delete("/watchlist/{eid}", status_code=204)
def delete_watchlist(eid: int):
    with closing(connect()) as con:
        _404(unwatch(con, eid), "watchlist entry")
