# Ghost Signal: Product Requirements Document

- Version: 1.0 (draft)
- Date: 18 Nov 2026
- Owner: Najwati (solo, non-student)
- Context: Kiroween 2026 hackathon, Frankenstein category
- Status: repo created, nothing else built yet. This PRD is the build spec.
  The builder (Hermes) must follow it. If reality differs from this PRD,
  update the PRD and the README Status section instead of hiding the gap.

## 1. Problem

Weak signals die unseen. A topic can appear in one paper, then a patent, then
a news article, and nobody connects the dots until the topic is already
mainstream. Analysts, product teams, journalists, and risk teams have no
cheap tool that watches faint topics across sources and shows the evidence
trail behind each one.

## 2. Users

- Research analysts tracking emerging topics.
- Product teams watching adjacent technologies.
- Journalists looking for stories before they break.
- Risk teams watching for early warnings.

## 3. Goals

1. Collect documents from public sources on a schedule and store them with
   full provenance (source, URL, timestamps).
2. Extract entities and relations with an evidence quote and source URL for
   every claim.
3. Score each entity with a transparent, four-component Ghost Score (0-100).
4. Show a feed ranked by score, with a clickable evidence chain per entity.
5. Let users keep a watchlist of entities they care about.
6. Run end to end with zero budget: no paid keys, heuristic extraction only
   in v1.

## 4. Non-goals (v1)

These are explicitly out of scope. Do not build them in v1:

- TradingView integration, Pine Script, chart indicators, or anything that
  renders on a trading chart. Ghost Signal is a research dashboard, not a
  trading tool.
- Price prediction, market forecasting, or buy/sell advice.
- Multi-language support (English only in v1).
- Email alerts or notifications.
- Neo4j or any external graph database (NetworkX in v1).
- User accounts, login, or payments.
- Mobile app.

## 5. Product overview

Ghost Signal is a pipeline plus a dashboard:

1. Collector fetches documents every ~4 hours.
2. Extractor finds entities and relations, each with evidence.
3. Knowledge graph links entities through relations.
4. Ghost Score engine scores entities daily.
5. FastAPI serves the feed, entity detail, score history, and watchlist.
6. Streamlit dashboard presents the feed, the evidence chain, and the
   watchlist.

The honest promise to users: Ghost Signal does not predict the future. It
makes sure a signal that already exists does not die unseen.

## 6. Functional requirements

### FR-1: Collector

- FR-1.1: Fetch documents from GDELT in M1. Add arXiv and Hacker News in M4.
  RSS is a stretch goal, not required for M4.
- FR-1.2: Run on a schedule (about every 4 hours) and on demand.
- FR-1.3: Store every document with source, source_type, title, URL,
  published_at, collected_at, raw_text, cleaned_text, and language.
- FR-1.4: Deduplicate by URL. Never store the same document twice.
- FR-1.5: Start with busy topics (AI, energy, health) so the graph fills
  immediately. Do not start with a super-niche topic.

### FR-2: Extractor

- FR-2.1: Extract entities of type company, technology, disease, product, or
  person.
- FR-2.2: Extract relations between entity pairs with a relation label and a
  claim text.
- FR-2.3: Every extracted claim MUST carry an evidence_quote (verbatim text
  from the source document) and the source URL. A claim without evidence is
  dropped, never stored, never shown.
- FR-2.4: v1 extractor is heuristic (keywords and regex). It must work end to
  end with zero cost and no API key.
- FR-2.5: The extractor is pluggable: one interface, two implementations
  (heuristic now, LLM later as a documented upgrade path only). Do not create
  accounts or API keys for the LLM path.

### FR-3: Knowledge graph

- FR-3.1: Build the graph with NetworkX. Nodes are entities, edges are
  relations with evidence.
- FR-3.2: The graph must answer: neighbours of an entity, the evidence chain
  for a relation, and the first-seen date per entity.
- FR-3.3: No external graph database in v1.

### FR-4: Ghost Score engine

- FR-4.1: Compute one score row per entity per day (novelty, velocity,
  corroboration, weirdness, ghost_score), so the trend is auditable.
- FR-4.2: Formula (exact, weights fixed in v1):

```
Ghost Score = (Novelty x 0.4) + (Velocity x 0.3)
            + (Corroboration x 0.2) + (Weirdness x 0.1)
```

- FR-4.3: Novelty: first appearance this week scores high; thousands of
  mentions scores low.
- FR-4.4: Velocity: how fast mentions are rising. 1 to 5 mentions in 7 days
  beats a flat 20 mentions.
- FR-4.5: Corroboration: independent, different-type sources (a paper plus a
  patent plus news) beat three articles copying one another.
- FR-4.6: Weirdness: appearing in an unexpected domain (for example battery
  tech in a medical journal) scores higher.
- FR-4.7: Score above 70 marks the top of the feed ("Rising from the grave" /
  "Signal strengthening"). Show all four components, not just the total.

### FR-5: API (FastAPI)

- FR-5.1: `GET /feed`: ranked feed of entities ordered by Ghost Score
  (not by time), with score and components.
- FR-5.2: `GET /entities/{id}`: entity detail with its evidence chain
  (documents in time order, each with its source link).
- FR-5.3: `GET /entities/{id}/scores`: score history per entity.
- FR-5.4: `POST /watchlist` and `DELETE /watchlist/{id}`: add and remove
  watchlist entries. `GET /watchlist`: list them.
- FR-5.5: Every API response that includes a claim also includes its
  evidence quote and source URL.

### FR-6: Dashboard (Streamlit)

- FR-6.1: Feed ordered by Ghost Score, not by time.
- FR-6.2: Click an entity to see its evidence chain: paper weeks ago, then
  patent, then news, each with its source link.
- FR-6.3: Show all four score components per entity.
- FR-6.4: Watchlist add and remove from the dashboard.
- FR-6.5: Dark Halloween styling is a plus. It must stay readable.
- FR-6.6: Seed with REAL collected data. No placeholder or fake signals
  anywhere in the dashboard.

### FR-7: Watchlist

- FR-7.1: A user can add any entity to the watchlist and remove it.
- FR-7.2: The watchlist shows the current score and components per entity.

## 7. Data model (v1, SQLite, exact)

- **documents**: id, source, source_type, title, url, published_at,
  collected_at, raw_text, cleaned_text, language (English only in v1)
- **entities**: id, name, type (company / technology / disease / product /
  person), first_seen_at, mention_count
- **relations**: id, doc_id, entity_a_id, entity_b_id, relation_label,
  claim_text, evidence_quote, created_at
- **scores**: entity_id, date, novelty, velocity, corroboration, weirdness,
  ghost_score (one row per entity per day)

## 8. Evidence rule (hard rule)

No claim is shown without its evidence quote and source URL. No evidence
means no signal. This applies to the graph, the API, and the dashboard alike.

## 9. UI requirements

- Feed ranked by score. Evidence chain view in time order. Watchlist view.
- Every entity shows its four score components.
- Dark theme, readable, coherent with the Halloween theme.
- All UI text in English.

## 10. Acceptance criteria (per milestone)

- **M1, by 20 Nov**: repo public with MIT licence and /.kiro present;
  collector plus SQLite running on GDELT; real documents in the database.
  Accept: `sqlite3 data/ghost-signal.db "SELECT COUNT(*) FROM documents;"`
  returns real rows with real URLs and timestamps.
- **M2, by 25 Nov**: heuristic extractor plus NetworkX graph plus Ghost
  Score. Accept: at least one entity with a full evidence chain (3 or more
  documents from at least 2 source types) and a computed score with all four
  components.
- **M3, by 29 Nov**: FastAPI plus Streamlit dashboard running locally; feed
  ordered by score; evidence chain view; watchlist works. Accept: a
  screenshot of the feed showing real signals, and the API returning JSON for
  the top entity.
- **M4, by 2 Dec**: arXiv plus Hacker News added; UI polish; README, Kiro
  write-up, and blog draft complete; feature freeze. Accept: README Status
  section is accurate; no placeholder data anywhere.
- **M5, by 4 Dec**: demo video recorded from the real dashboard (under 3
  minutes), uploaded to public YouTube; Devpost submission draft saved; blog
  published. Accept: the submission checklist is fully ticked except the
  final submit click, which is Naj's.

## 11. Constraints

1. Zero budget: no paid API keys, no spending, no sign-ups that cost money.
2. English only in v1 (code, docs, dashboard, video, submission).
3. Never invent results, metrics, or evaluation numbers. If something has not
   run, say so plainly in the README Status section.
4. No em dashes in code comments, docs, README, video script, or anything
   written for this project.
5. The repo must contain /.kiro at the root (specs, hooks, steering). Never
   add /.kiro to .gitignore. This is a submission requirement and can
   disqualify the entry.
6. Do not reuse or copy the payment-ledger API repo or any prior work as the
   entry. Reusing general skills (Python pipelines, FastAPI, SQL) is fine.
7. Kiro usage must be real, deep, and documented (specs, steering, hooks,
   agents, experiments). Insufficient Kiro use can disqualify the entry.
8. No Kiro credit request or resubmission. Build with the credits already
   connected on Naj's VPS.

## 12. Risks and open questions

- R1: Heuristic extraction quality on real news text. Mitigation: start with
  busy topics, validate against the evidence chain, keep the extractor
  pluggable.
- R2: GDELT volume and noise. Mitigation: deduplicate by URL, filter by
  language (English), cap the daily intake.
- R3: Dashboard with no real data looks empty. Mitigation: run the collector
  first and verify real rows before calling any UI work done.
- R4: Model quality of the build agent. Mitigation: this PRD plus the README
  are the spec. If a step is unclear, read them again before acting. Do not
  guess the product from its name alone.
- Open question: deployment target for the judges (Streamlit Community Cloud
  vs demo link with run instructions). Decided by Naj before M5.

## 13. Out of scope (v2)

Multi-language support, price prediction, email alerts, Neo4j, user accounts,
mobile app, RSS feed reader UI.
