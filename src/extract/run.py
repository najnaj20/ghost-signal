"""Extract entities and relations for documents not processed yet."""
from datetime import datetime, timezone

from src.db import connect
from src.extract.heuristic import HeuristicExtractor


def entity_id(con, e, when):
    con.execute("INSERT OR IGNORE INTO entities (name, type, first_seen_at) VALUES (?, ?, ?)", (e.name, e.type, when))
    return con.execute("SELECT id FROM entities WHERE name = ? AND type = ?", (e.name, e.type)).fetchone()[0]


def run(con, extractor=None):
    extractor = extractor or HeuristicExtractor()
    now = datetime.now(timezone.utc).isoformat()
    docs = con.execute("SELECT id, cleaned_text, COALESCE(published_at, collected_at) FROM documents "
                       "WHERE id NOT IN (SELECT doc_id FROM relations)").fetchall()
    n = 0
    for doc_id, text, when in docs:
        for c in extractor.extract(text):
            a, b = entity_id(con, c.a, when), entity_id(con, c.b, when)
            con.execute("INSERT INTO relations (doc_id, entity_a_id, entity_b_id, relation_label, claim_text, "
                        "evidence_quote, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (doc_id, a, b, c.label, c.claim_text, c.evidence_quote, now))
            n += 1
    # first_seen_at and mention_count are derived from the evidence, so they stay correct on reruns.
    con.execute("""UPDATE entities SET
        first_seen_at = (SELECT MIN(COALESCE(d.published_at, d.collected_at)) FROM relations r JOIN documents d
                         ON d.id = r.doc_id WHERE r.entity_a_id = entities.id AND r.entity_b_id = entities.id),
        mention_count = (SELECT COUNT(DISTINCT r.doc_id) FROM relations r
                         WHERE r.entity_a_id = entities.id AND r.entity_b_id = entities.id)""")
    con.commit()
    return len(docs), n


if __name__ == "__main__":
    c = connect()
    docs, claims = run(c)
    e = c.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    print(f"documents processed: {docs}, claims stored: {claims}, entities total: {e}")
