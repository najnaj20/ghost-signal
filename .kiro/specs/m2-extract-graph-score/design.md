# M2 design

- Extractor: gazetteer (about 200 terms) plus regex for company suffixes, titled persons,
  disease suffixes, coined names (CamelCase, caps plus digits) and defined acronyms.
- Sentence split; each mention becomes a self relation (entity_a = entity_b, label mentioned_in)
  so the schema stays fixed; adjacent pairs in a sentence become typed relations by verb regex.
- keep() checks evidence_quote is a substring of the document text. DB CHECK blocks empty quotes.
- first_seen_at and mention_count are recomputed from relations after every run.
- Score, each component 0 to 100:
  - Novelty = 100 x max(0, 1 - age_days/30) x 1/(1 + log10(mentions))
  - Velocity = 100 x recent/(recent + prior week) x min(1, recent/3)
  - Corroboration = 100 x (0.7 x source_types/3 + 0.3 x min(outlets, 5)/5)
  - Weirdness = 100 x min(1, 1.5 x (1 - share of the biggest topic))
