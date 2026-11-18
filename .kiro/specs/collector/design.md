# Collector design (M1)

- GDELT DOC 2.0 API, mode=artlist, format=json, timespan=24h, maxrecords=75 per topic.
- url is UNIQUE in SQLite; inserts use INSERT OR IGNORE, so dedup is a DB constraint.
- published_at comes from GDELT seendate (UTC). collected_at is run time (UTC).
- raw_text keeps the full GDELT article record as JSON plus the topic.
- cleaned_text is the normalized headline. The DOC API returns no article body;
  fetching bodies is a later upgrade if the extractor needs it.
- One failed topic is logged and skipped; the run continues.
