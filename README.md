# Ghost Signal

An agentic AI that hunts "ghost signals": topics that are still faint and rarely
mentioned, but starting to move across news, papers, and tech sources. It turns
them into an evidence-backed early-warning dashboard.

Built for **Kiroween 2026**, Frankenstein category, by Najwati (solo, non-student).

## The honest promise

Ghost Signal does not predict the future. It makes sure a signal that already
exists does not die unseen.

## What this is NOT

Read this first, because it prevents the most common misunderstanding:

- This is **not a TradingView indicator**. There is no TradingView integration,
  no Pine Script, and no chart indicator anywhere in this project.
- This is **not a trading bot** and it does not give buy or sell signals.
- It does **not predict prices** or forecast markets.
- It is a research tool: it collects documents, extracts entities and relations,
  scores how new and fast-moving each entity is, and shows the evidence behind
  every score.

## How it works

```
GDELT / arXiv API / Hacker News API / RSS
        |  (collector, Python, scheduled every ~4h)
SQLite (documents, entities, relations, scores)
        |  (extractor, pluggable: heuristic fallback first, LLM later)
Knowledge graph (NetworkX, NOT Neo4j in v1)
        |  (Ghost Score engine, Python)
FastAPI API + Streamlit dashboard (feed, evidence chain, watchlist)
```

1. **Collector** fetches documents from public sources (GDELT first, then arXiv
   and Hacker News).
2. **Extractor** pulls entities (company, technology, disease, product, person)
   and relations out of each document, always with an evidence quote and a
   source URL.
3. **Knowledge graph** (NetworkX) links entities through their relations.
4. **Ghost Score engine** scores every entity from 0 to 100.
5. **API + dashboard** show the ranked feed, the evidence chain for each
   entity, and a watchlist.

## Ghost Score (0 to 100)

```
Ghost Score = (Novelty x 0.4) + (Velocity x 0.3)
            + (Corroboration x 0.2) + (Weirdness x 0.1)
```

- **Novelty (40%)**: how new is this entity? First appearance this week scores
  high; thousands of mentions scores low.
- **Velocity (30%)**: how fast are mentions rising? 1 to 5 mentions in 7 days
  beats a flat 20 mentions.
- **Corroboration (20%)**: independent, different-type sources (a paper plus a
  patent plus news) beat three articles copying one another.
- **Weirdness / cross-domain (10%)**: appearing in an unexpected domain (for
  example battery tech in a medical journal) scores higher.
- **Score above 70** = top of the feed ("Rising from the grave" / "Signal
  strengthening"). The dashboard shows all four components, not just the total.

## The evidence rule

No claim is shown without its evidence quote and source URL. No evidence means
no signal. Every relation in the graph carries the quote and the link it came
from. If the extractor cannot find evidence for a claim, the claim is dropped.

## Repo layout

```
README.md, PRD.md, LICENSE (MIT), .gitignore, requirements.txt
.kiro/                  specs, steering, hooks, agents (Kiro)
src/collector/          document collection (GDELT, arXiv, Hacker News, RSS)
src/extract/            entity and relation extraction (heuristic first)
src/graph/              NetworkX knowledge graph
src/score/              Ghost Score engine
src/api/                FastAPI API
src/dashboard/          Streamlit dashboard
data/                   SQLite file (gitignored; seed data documented)
tests/
docs/                   blog draft, video script, submission checklist
```

## Quickstart

Prerequisites: Python 3.11 or newer.

```bash
git clone https://github.com/najnaj20/ghost-signal
cd ghost-signal
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline (collector, then extractor and scorer, then the app):

```bash
python -m src.collector.run
python -m src.extract.run
python -m src.score.run
uvicorn src.api.main:app --reload
streamlit run src/dashboard/app.py
```

The dashboard runs on `http://localhost:8501` and the API on
`http://localhost:8000` by default.

## Data model (v1, SQLite)

- **documents**: id, source, source_type, title, url, published_at,
  collected_at, raw_text, cleaned_text, language (English only in v1)
- **entities**: id, name, type (company / technology / disease / product /
  person), first_seen_at, mention_count
- **relations**: id, doc_id, entity_a_id, entity_b_id, relation_label,
  claim_text, evidence_quote, created_at
- **scores**: entity_id, date, novelty, velocity, corroboration, weirdness,
  ghost_score (one row per entity per day, so the trend is auditable)

## Extractor: heuristic first, LLM later

The v1 extractor is heuristic (keywords and regex). It must work end to end
with zero cost and no API key. The extractor is pluggable: an LLM
implementation is a documented upgrade path only. Do not create accounts or
API keys for it. The dashboard must show real signals with the heuristic
extractor alone.

## Kiro usage

This project is built using Kiro. The evidence lives in `/.kiro`:

- `/.kiro/specs/` : requirements, design, and tasks documents per feature
- `/.kiro/steering/` : product, tech, and structure guidance
- `/.kiro/hooks/` : automated workflows used during the build
- `/.kiro/agents/` : custom agents used

The full "how Kiro was used" write-up (IDE/CLI/Web/Crew, custom agents,
hooks, spec-driven development, steering, MCP, property-based testing, Kiro
powers) is documented in `docs/kiro-experiments.md` as the build progresses.
Nothing is claimed about Kiro use that did not actually happen.

## Status

Updated 18 Nov 2026. Be honest about what is done and what is not.

- Done: public repo created (18 Nov 2026), MIT licence, README and PRD written.
- Not done: collector, extractor, graph, scorer, API, dashboard. No data has
  been collected yet and no score has been computed. Do not claim otherwise.

## Milestones

- **M1, by 20 Nov**: repo created (public, MIT, /.kiro present); collector
  plus SQLite running on GDELT; real documents in the database.
- **M2, by 25 Nov**: heuristic extractor plus NetworkX graph plus Ghost Score.
  At least one entity with a full evidence chain (3 or more documents from at
  least 2 source types) and a computed score with all four components.
- **M3, by 29 Nov**: FastAPI plus Streamlit dashboard running locally; feed
  ordered by score; evidence chain view; watchlist works.
- **M4, by 2 Dec**: arXiv plus Hacker News added; UI polish; README, Kiro
  write-up, and blog draft complete; feature freeze.
- **M5, by 4 Dec**: demo video recorded from the real dashboard (under 3
  minutes), uploaded to public YouTube; Devpost submission draft saved.

Submission closes Saturday 5 Dec 2026, 06:00 WITA.

## Rules for this repo

1. Zero budget: no paid API keys, no spending, no sign-ups that cost money.
2. English only in v1 (code, docs, dashboard, video, submission).
3. Never invent results, metrics, or evaluation numbers. If something has not
   run, say so plainly in the Status section above.
4. No em dashes in code comments, docs, README, video script, or anything
   written for this project.

## Licence

MIT. See LICENSE.
