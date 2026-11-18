# Collector requirements (M1)

1. Fetch English documents from GDELT for busy topics: ai, energy, health (FR-1.1, FR-1.5).
2. Run on demand and on a repeat interval of about 4 hours (FR-1.2).
3. Store source, source_type, title, url, published_at, collected_at, raw_text,
   cleaned_text, language for every document (FR-1.3).
4. Deduplicate by URL (FR-1.4). Cap intake per topic per run (R2).
