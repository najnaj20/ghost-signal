"""Hacker News collector via the Algolia HN Search API. source_type: forum."""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from src.collector.gdelt import store

API = "https://hn.algolia.com/api/v1/search_by_date"
# Algolia has no OR operator, so each topic is a few plain queries.
TOPICS = {
    "ai": ["LLM", "machine learning", "AI model"],
    "energy": ["battery", "solar", "nuclear", "hydrogen"],
    "health": ["vaccine", "clinical trial", "outbreak"],
}
PER_QUERY = 25
WINDOW_S = 7 * 86400


def fetch(query, per_query=PER_QUERY):
    since = int(time.time()) - WINDOW_S
    q = urllib.parse.urlencode({"query": query, "tags": "story", "hitsPerPage": per_query,
                                "numericFilters": f"created_at_i>{since}"})
    with urllib.request.urlopen(f"{API}?{q}", timeout=30) as r:
        return json.load(r).get("hits", [])


def to_row(hit, topic, collected_at):
    title = " ".join((hit.get("title") or "").split())
    if not title or not hit.get("objectID"):
        return None
    # url is the HN discussion, so it never collides with the same story collected from GDELT.
    return {
        "source": "hackernews", "source_type": "forum", "title": title,
        "url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
        "published_at": datetime.fromtimestamp(hit["created_at_i"], timezone.utc).isoformat(),
        "collected_at": collected_at,
        "raw_text": json.dumps({"topic": topic, "story_url": hit.get("url"), "points": hit.get("points")}),
        "cleaned_text": title, "language": "en",
    }


def collect(con, topics=TOPICS):
    now = datetime.now(timezone.utc).isoformat()
    total = 0
    for topic, queries in topics.items():
        for q in queries:
            try:
                hits = fetch(q)
            except Exception as e:
                print(f"[hn:{topic}:{q}] fetch failed: {e}")
                continue
            added = store(con, [r for h in hits if (r := to_row(h, topic, now))])
            total += added
            print(f"[hn:{topic}:{q}] fetched {len(hits)}, new {added}")
            time.sleep(1)
    return total
