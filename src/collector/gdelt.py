"""GDELT DOC 2.0 API collector (https://api.gdeltproject.org/api/v2/doc/doc)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://api.gdeltproject.org/api/v2/doc/doc"
# FR-1.5: busy topics first so the graph fills fast.
TOPICS = {
    "ai": '("artificial intelligence" OR "machine learning" OR "large language model")',
    "energy": '("battery" OR "solar power" OR "nuclear energy" OR "hydrogen fuel")',
    "health": '("vaccine" OR "clinical trial" OR "outbreak" OR "drug approval")',
}
MAX_PER_TOPIC = 75  # R2: cap daily intake
RATE_LIMIT_S = 6  # GDELT asks for at most one request every 5 seconds


def fetch(query, max_records=MAX_PER_TOPIC, timespan="24h"):
    params = {
        "query": f"{query} sourcelang:english",
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "timespan": timespan,
        "sort": "datedesc",
    }
    req = urllib.request.Request(
        API + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "ghost-signal/0.1 (Kiroween 2026)"},
    )
    body = ""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(RATE_LIMIT_S * 2 ** (attempt + 1))  # 429: back off 12/24/48s
    try:
        return json.loads(body).get("articles", [])
    except json.JSONDecodeError:
        raise RuntimeError(f"GDELT non-JSON reply: {body[:200]}")


def to_iso(seendate):
    """GDELT seendate '20261118T093000Z' to ISO 8601 UTC."""
    return datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()


def to_row(article, topic, collected_at):
    title = " ".join((article.get("title") or "").split())
    lang = (article.get("language") or "").lower()
    if not article.get("url", "").startswith("http") or lang not in ("english", "en"):
        return None
    # ponytail: DOC API has no article body, so cleaned_text is the headline.
    # Upgrade: fetch body text when the extractor needs more than headlines.
    return {
        "source": f"gdelt:{article.get('domain', '')}",
        "source_type": "news",
        "title": title,
        "url": article["url"],
        "published_at": to_iso(article["seendate"]) if article.get("seendate") else None,
        "collected_at": collected_at,
        "raw_text": json.dumps({**article, "topic": topic}, ensure_ascii=False),
        "cleaned_text": title,
        "language": "en",
    }


def store(con, rows):
    cols = "source, source_type, title, url, published_at, collected_at, raw_text, cleaned_text, language"
    before = con.total_changes
    con.executemany(
        f"INSERT OR IGNORE INTO documents ({cols}) VALUES "
        "(:source, :source_type, :title, :url, :published_at, :collected_at, :raw_text, :cleaned_text, :language)",
        rows,
    )
    con.commit()
    return con.total_changes - before


def collect(con, topics=TOPICS):
    now = datetime.now(timezone.utc).isoformat()
    total = 0
    for i, (topic, query) in enumerate(topics.items()):
        if i:
            time.sleep(RATE_LIMIT_S)
        try:
            articles = fetch(query)
        except Exception as e:  # one failed topic must not kill the run
            print(f"[{topic}] fetch failed: {e}")
            continue
        rows = [r for a in articles if (r := to_row(a, topic, now))]
        added = store(con, rows)
        total += added
        print(f"[{topic}] fetched {len(articles)}, new {added}")
    return total
