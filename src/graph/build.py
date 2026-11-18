"""NetworkX knowledge graph (FR-3). Nodes are entities, edges are relations with evidence."""
import networkx as nx

from src.db import connect

EVIDENCE_SQL = """SELECT d.id, d.title, d.url, d.source, d.source_type, COALESCE(d.published_at, d.collected_at),
       r.relation_label, r.claim_text, r.evidence_quote
FROM relations r JOIN documents d ON d.id = r.doc_id"""


def build(con):
    g = nx.MultiGraph()
    for eid, name, typ, first, n in con.execute("SELECT id, name, type, first_seen_at, mention_count FROM entities"):
        g.add_node(eid, name=name, type=typ, first_seen_at=first, mention_count=n)
    for a, b, label, claim, quote, doc_id, url in con.execute(
            "SELECT r.entity_a_id, r.entity_b_id, r.relation_label, r.claim_text, r.evidence_quote, r.doc_id, d.url "
            "FROM relations r JOIN documents d ON d.id = r.doc_id WHERE r.entity_a_id != r.entity_b_id"):
        g.add_edge(a, b, label=label, claim_text=claim, evidence_quote=quote, doc_id=doc_id, url=url)
    return g


def neighbours(g, eid):
    return sorted(g.neighbors(eid), key=lambda n: g.nodes[n]["name"])


def relation_evidence(g, a, b):
    """Evidence chain for one relation: every edge between a and b, each with quote and URL."""
    return [d for d in g.get_edge_data(a, b, default={}).values()]


def evidence_chain(con, eid):
    """All documents that mention an entity, oldest first, each with quote and source URL (FR-6.2)."""
    rows = con.execute(EVIDENCE_SQL + " WHERE r.entity_a_id = ? AND r.entity_b_id = ? ORDER BY 6, 1", (eid, eid))
    keys = ("doc_id", "title", "url", "source", "source_type", "published_at", "relation_label", "claim_text",
            "evidence_quote")
    return [dict(zip(keys, r)) for r in rows]


if __name__ == "__main__":
    g = build(connect())
    print(f"nodes: {g.number_of_nodes()}, edges: {g.number_of_edges()}")
