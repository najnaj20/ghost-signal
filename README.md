# Ghost Signal

An agentic AI that hunts "ghost signals": topics that are still faint and rarely
mentioned, but starting to move across news, papers, and tech sources. It turns
them into an evidence-backed early-warning dashboard.

Built for **Kiroween 2026**, Frankenstein category, by a solo entrant (non-student).

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
.kiro/                  specs and steering (Kiro)
src/collector/          document collection (GDELT, arXiv, Hacker News, RSS)
src/extract/            entity and relation extraction (heuristic first)
src/graph/              NetworkX knowledge graph
src/score/              Ghost Score engine
src/api/                FastAPI API
src/dashboard/          Streamlit dashboard
data/                   SQLite file (gitignored; seed data documented)
tests/
docs/                   blog draft, milestone evidence (m3/, m4/)
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

## How Kiro was used

This section only lists what actually happened. Where a Kiro feature was not
used, it says so.

The build runs on a Linux VPS. The coding agent doing the work is Hermes Agent
(Nous Research). Its model calls go through a local OpenAI-compatible router
(9router) to a Kiro provider connection, so the model work for this build is
served by the Kiro credits connected on the VPS (model `kr/claude-opus-5.5`).
No Kiro IDE or Kiro CLI binary is installed on the VPS.

1. **Kiro IDE / CLI / Web / Crew.** None of these were run on the VPS. Kiro
   was used as the model backend through the Kiro provider connection. The
   IDE, CLI, Web and Crew products were not compared in this build, so there
   is no difference between them to report.
2. **Custom agents.** None created. There is no `/.kiro/agents/` directory.
3. **Agent hooks.** None created. There is no `/.kiro/hooks/` directory.
   Tests and the pipeline were run by hand (by the build agent), not by hooks.
4. **Spec-driven development.** Yes. Each milestone with real logic got a
   spec in `/.kiro/specs/<feature>/` with three files in Kiro's format:
   `requirements.md` (numbered requirements that point back to PRD FR ids),
   `design.md` (concrete decisions, for example URL dedup as a SQLite UNIQUE
   constraint), and `tasks.md` (checkbox tasks, each ending in a runnable
   check). Specs exist for `collector` (M1) and `m2-extract-graph-score`
   (M2). M3 and M4 have no spec; M3 was built straight from PRD FR-5 and FR-6.
   The specs were written by the build agent, not generated by the Kiro IDE.
5. **Steering docs.** Three files in `/.kiro/steering/`: `product.md`,
   `tech.md`, `structure.md`. The most useful was `product.md`, because its
   short "not a trading tool, no prices, no forecasts" line and "PRD.md is the
   spec of record" rule kept every milestone inside scope. `tech.md` fixed the
   schema and the GDELT rate limit, which mattered once GDELT started
   answering HTTP 429.
6. **MCP.** Not used for this project. No MCP server is part of the build.
7. **Property-based testing.** Not used. Tests are plain assert scripts
   (`tests/test_collector.py`, `tests/test_m2.py`, `tests/test_m3.py`).

## Status

Updated 21 Nov 2026. Feature freeze since M4: only fixes from here on.

- Done (M1): GDELT collector (`python -m src.collector.run`, or `--every 4`
  to repeat) and SQLite database at `data/ghost-signal.db` with the PRD
  schema, deduplicated by URL.
- Done (M2): arXiv (paper) and Hacker News (forum) collectors, heuristic
  extractor, NetworkX graph, Ghost Score engine.
- Done (M3): FastAPI API (`uvicorn src.api.main:app`) and Streamlit dashboard
  (`streamlit run src/dashboard/app.py`). Feed by Ghost Score, evidence chain,
  watchlist.
- Done (M4, 21 Nov 2026): second day of data collected; dashboard polish
  (Signal column shows "Rising from the grave" above 70, one decimal on all
  score columns, Watched column is plain text so it is not confused with the
  row selector); README Kiro write-up; blog draft in
  `docs/blog-post-draft.md`. Data after the refresh: 674 documents, 324
  entities, 856 relations, score rows for 2026-11-18 (215) and 2026-11-21
  (324). Two entities now score above 70. Details in PROGRESS.md and
  `docs/m4/`.
- Tests: `python -m tests.test_collector`, `python -m tests.test_m2`,
  `python -m tests.test_m3`.

Not done yet:

- No scheduler (cron or systemd) is installed. Collection only happened on
  18 Nov and 21 Nov 2026, so novelty and velocity still rest on two days.
- No patent source, no RSS source.
- GDELT often answers HTTP 429. On 21 Nov only the ai topic came back; energy
  and health were skipped.
- The GDELT DOC API gives headlines, not article bodies, so news
  `cleaned_text` is the headline.
- The heuristic extractor misses many entities and some hits are generic
  (for example "robotics", "GitHub"). No LLM extractor.
- M5 not started: no demo video, no Devpost draft, blog not published.

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
