# Progress

## M1: done (commit 3c1c06a)
GDELT collector and SQLite schema (PRD section 7).

## M2: done (commit 5539aca)
arXiv and Hacker News collectors, heuristic extractor, NetworkX graph, Ghost Score.
Database at start of M3: 407 documents, 215 entities, 525 relations, 215 score rows (all dated 2026-11-18).

## M3: done (21 Nov 2026)
FastAPI API (FR-5) in src/api/main.py and Streamlit dashboard (FR-6) in src/dashboard/app.py.
Both read the real M2 data; no seed or placeholder data was added. The scorer was not changed.

Schema addition: one new table, watchlist (entity_id PRIMARY KEY, added_at), in src/db.py.
The PRD tables and columns are unchanged.

### API endpoints
Run: uvicorn src.api.main:app --reload (http://localhost:8000)
- GET /feed?limit=50: entities ordered by latest ghost_score, with novelty, velocity, corroboration,
  weirdness, and latest_evidence (evidence_quote plus url).
- GET /entities/{id}: entity detail plus evidence_chain (documents oldest first, each with url,
  source_type, evidence_quote) and claims (relations to other entities, each with evidence_quote and url).
- GET /entities/{id}/scores: score history, one row per day.
- GET /watchlist, POST /watchlist {"entity_id": N} (201), DELETE /watchlist/{id} (204). Unknown ids return 404.
- Evidence rule: an entity with no evidence quote and source URL is left out of every response.

### Dashboard
Run: streamlit run src/dashboard/app.py (http://localhost:8501)
Feed ordered by Ghost Score, row click opens the evidence chain with source links, all four components
shown as metrics, add and remove watchlist buttons, dark theme from .streamlit/config.toml.

### Verification (21 Nov 2026, VPS)
- Tests: python -m tests.test_collector, python -m tests.test_m2, python -m tests.test_m3: all print ok.
- curl GET /feed and GET /entities/17 returned real JSON: docs/m3/feed_top3.json, docs/m3/entity_17.json.
- curl POST /watchlist 201, GET /watchlist listed entity 17, DELETE 204, GET /watchlist then [].
  Unknown entity returned 404.
- Dashboard screenshot from headless Chromium: docs/m3/dashboard_feed.png. A Playwright run clicked
  Add to watchlist, saw "Watchlist (1)", clicked Remove, saw "Watchlist (0)".
- Top 10 from GET /feed (docs/m3/feed_top10.txt):

 1.  69.3  robotics (technology)  N=75.1 V=66.7 C=58.7 W=75.0  http://arxiv.org/abs/2611.23228v1
 2.  69.2  GitHub (product)  N=74.9 V=66.7 C=58.7 W=75.0  http://arxiv.org/abs/2611.23216v1
 3.  68.2  OpenAI (company)  N=66.2 V=100.0 C=58.7 W=0.0  https://news.ycombinator.com/item?id=50542368
 4.  68.2  GPT-6 (product)  N=72.4 V=66.7 C=58.7 W=75.0  https://news.ycombinator.com/item?id=50535783
 5.  64.1  Apple (company)  N=61.6 V=100.0 C=47.3 W=0.0  https://whdh.com/news/apple-joins-a-parade-of-technology-hiccups-in-recent-days/
 6.  64.0  Microsoft (company)  N=61.1 V=100.0 C=29.3 W=37.5  https://news.ycombinator.com/item?id=50543279
 7.  63.1  measles (disease)  N=44.4 V=100.0 C=76.7 W=0.0  https://midmichigannow.com/news/nation-world/preventable-failure-us-loses-measles-elimination-status-after-26-years
 8.  62.2  fine-tuning (technology)  N=42.9 V=100.0 C=58.7 W=33.3  https://news.ycombinator.com/item?id=50543212
 9.  61.7  transformer (technology)  N=70.7 V=66.7 C=29.3 W=75.0  http://arxiv.org/abs/2611.23126v1
10.  60.1  reinforcement learning (technology)  N=44.4 V=100.0 C=29.3 W=64.3  http://arxiv.org/abs/2611.23124v1

### Known gaps
- No entity scores above 70 yet, so no "Rising from the grave" label shows. All data is from one day
  of collection; novelty and velocity need several days.
- No patent source exists yet, so evidence chains show paper, forum, and news only.
- Some heuristic hits are generic (robotics, GitHub) and rank high on one day of data.


## Identity cleanup (commit f0884b5, 21 Nov 2026)
Personal name removed from PRD.md and README.md file contents ("solo entrant (non-student)").
Repo-wide grep (excluding .git and .venv) for the name, personal email, home city, university and phone
returns zero matches. Git history was not rewritten; past commit authors are unchanged.

## M4: done (21 Nov 2026)
No M1, M2 or M3 code was changed. arXiv and Hacker News collectors already existed from M2.

### Data refresh (second day)
python -m src.collector.run: new documents 267, total 674.
- GDELT: ai fetched 75, new 75. energy and health failed with "HTTP Error 429: Too Many Requests"
  and were skipped by the existing back off. Not retried.
- arXiv: ai 50 new, energy 16 new, health 9 new. Hacker News: 117 new across 10 queries.
python -m src.extract.run: documents processed 456, claims stored 331, entities total 324.
python -m src.score.run: entities scored 324.
Database now: 674 documents (2026-11-18: 407, 2026-11-21: 267), 324 entities, 856 relations,
539 score rows (215 dated 2026-11-18, 324 dated 2026-11-21). 2 entities score above 70.
Backup of the M3 database before the refresh was kept outside the repo (data/ is gitignored).

### Dashboard polish
Contrast was already fine: body, caption and metric text compute to #e8e6f0 on #0f0f14, links #b48cff,
headings #ff8c1a, evidence meta #a8a4b8. Changes in src/dashboard/app.py:
- New Signal column shows "Rising from the grave" for scores above 70 (it was only in the detail panel).
- All score columns use one decimal (mixed 100 / 58.7 before).
- Watched column is plain text "yes" instead of a checkbox, so it is not confused with the row selector.
Screenshot: docs/m4/dashboard_feed.png (headless Chromium via Playwright).

### Docs
README Status rewritten (M1 to M4 done, not done list) and "How Kiro was used" write-up added.
Blog draft: docs/blog-post-draft.md (not published).

### Verification (21 Nov 2026, VPS)
- python -m tests.test_collector, python -m tests.test_m2, python -m tests.test_m3: all print ok, exit 0.
- uvicorn src.api.main:app, curl GET /feed returned HTTP 200 with real JSON; top 10 in docs/m4/feed_top10.txt.
- streamlit run src/dashboard/app.py: /_stcore/health 200; screenshot shows feed ordered
  71.2, 70.3, 66.2, ... descending, no errors.
- Top 10 from GET /feed:

 1.   71.2  robotics (technology)  N=54.9 V=100.0 C=58.7 W=75.0  http://arxiv.org/abs/2611.26420v1
 2.   70.3  GPT-6 (product)  N=52.7 V=100.0 C=58.7 W=75.0  http://arxiv.org/abs/2611.26613v1
 3.   66.2  GitHub (product)  N=67.4 V=66.7 C=58.7 W=75.0  http://arxiv.org/abs/2611.23216v1
 4.   65.6  OpenAI (company)  N=59.6 V=100.0 C=58.7 W=0.0  https://news.ycombinator.com/item?id=50542368
 5.   64.3  Claude (product)  N=24.8 V=91.7 C=94.0 W=80.8  http://www.pakistantelegraph.com/news/279446523/frontier-breached-anthropic-mathematician-claims-solution-of-riemann-hypothesis-with-help-from-claude-ai
 6.   63.7  Anthropic (company)  N=45.9 V=100.0 C=76.7 W=0.0  http://www.pakistantelegraph.com/news/279446523/frontier-breached-anthropic-mathematician-claims-solution-of-riemann-hypothesis-with-help-from-claude-ai
 7.   62.5  TreeC (product)  N=72.7 V=66.7 C=29.3 W=75.0  http://arxiv.org/abs/2611.26441v1
 8.   62.3  Cursor (product)  N=66.0 V=100.0 C=29.3 W=0.0  https://news.ycombinator.com/item?id=50583519
 9.   61.7  Apple (company)  N=55.6 V=100.0 C=47.3 W=0.0  https://whdh.com/news/apple-joins-a-parade-of-technology-hiccups-in-recent-days/
10.   61.6  Microsoft (company)  N=55.0 V=100.0 C=29.3 W=37.5  https://news.ycombinator.com/item?id=50543279

## Feature freeze (from 21 Nov 2026)
After M4 no new features. Only fixes until submission.
