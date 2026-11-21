# Ghost Signal: catching faint topics before they go mainstream

Draft. Not published. Written as part of the Kiroween 2026 hackathon
(Frankenstein category).

## The idea

A topic often shows up first in one paper, then in a forum thread, then in a
news headline. By the time someone connects the three, it is already
mainstream. Ghost Signal watches public sources for these faint topics and
ranks them by a transparent score, with the evidence behind every claim.

It does not predict anything. It is not a trading tool and gives no price
forecasts. Its promise is smaller: a signal that already exists should not
die unseen.

## What it does

1. Collectors pull documents from GDELT (news), arXiv (papers) and Hacker
   News (forum) for three busy topics: ai, energy and health. Every document
   keeps its source, URL and timestamps. Duplicates are dropped by a UNIQUE
   constraint on the URL.
2. A heuristic extractor (keywords and regex, no API key, zero cost) pulls
   entities and relations. Every claim keeps a verbatim evidence quote. A
   claim without evidence is never stored.
3. NetworkX links entities into a graph.
4. The Ghost Score engine scores each entity from 0 to 100:
   Novelty x 0.4 + Velocity x 0.3 + Corroboration x 0.2 + Weirdness x 0.1.
   One row per entity per day, so the trend can be audited.
5. A FastAPI API and a Streamlit dashboard show the feed ranked by score,
   the evidence chain in time order, and a watchlist.

## Where it stands

After two collection days (18 Nov and 21 Nov 2026) the database holds 674
documents, 324 entities and 856 evidence-backed relations. Two entities now
score above 70 and carry the "Rising from the grave" label: robotics (71.2)
and GPT-6 (70.3). Both are partly generic heuristic hits, which is a known
weakness of the keyword extractor. Two days of data are not enough for
novelty and velocity to mean much yet; that needs a scheduler and more days.

GDELT rate limits hard. On the second run it answered HTTP 429 for the
energy and health topics, so only the ai news topic was refreshed. The
collector logs the failure, skips the topic and keeps going.

## How Kiro was used

Honest version, because the hackathon asks for real Kiro use and it is easy
to overclaim:

- The build agent (Hermes Agent, running on a Linux VPS) sends its model
  calls through a local router to a Kiro provider connection, so the model
  work is served by Kiro credits. No Kiro IDE or Kiro CLI was installed on
  the VPS, and Kiro Web and Crew were not used.
- Spec-driven development: the collector (M1) and the extractor, graph and
  score work (M2) each have a spec in `.kiro/specs/` with requirements,
  design and tasks. Requirements point back to PRD ids, and every task ends
  in a runnable check. M3 and M4 had no spec.
- Steering: three short files in `.kiro/steering/`. The product file helped
  most. One line, "not a trading tool, no prices, no forecasts", plus "PRD.md
  is the spec of record", kept every milestone in scope.
- Not used: custom agents, agent hooks, MCP, property-based testing. Tests
  are plain assert scripts.

## What is next

Feature freeze is on. Before submission the plan is fixes only, then a demo
video recorded from the real dashboard.
