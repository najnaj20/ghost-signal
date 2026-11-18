# M2 requirements: extractor, graph, Ghost Score

1. Heuristic extractor, no key, no cost (FR-2.4), behind one interface (FR-2.5).
2. Entity types: company, technology, disease, product, person (FR-2.1).
3. Every claim carries a verbatim evidence_quote; claims without one are dropped (FR-2.3).
4. NetworkX graph: neighbours, relation evidence, first-seen date (FR-3.2).
5. One score row per entity per day with four components and the fixed weights (FR-4).
6. Accept: one entity with 3+ documents from 2+ source types and a full score (PRD 10, M2).
