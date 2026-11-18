"""Compute today's Ghost Score row for every entity."""
from src.db import connect
from src.score.engine import score_all

if __name__ == "__main__":
    con = connect()
    print(f"entities scored: {score_all(con)}")
    for name, typ, g, n, v, c, w in con.execute(
            "SELECT e.name, e.type, s.ghost_score, s.novelty, s.velocity, s.corroboration, s.weirdness "
            "FROM scores s JOIN entities e ON e.id = s.entity_id WHERE s.date = (SELECT MAX(date) FROM scores) "
            "ORDER BY s.ghost_score DESC LIMIT 10"):
        print(f"{g:5.1f}  {name} ({typ})  N={n} V={v} C={c} W={w}")
