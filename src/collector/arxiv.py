"""arXiv API collector (https://export.arxiv.org/api/query). source_type: paper."""
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from src.collector.gdelt import store

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
TOPICS = {
    "ai": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG",
    "energy": 'abs:battery OR abs:"solar cell" OR abs:"hydrogen fuel" OR abs:"nuclear fusion"',
    "health": 'abs:vaccine OR abs:"clinical trial" OR abs:outbreak OR abs:epidemic',
}
MAX_PER_TOPIC = 50
RATE_LIMIT_S = 4  # arXiv asks for at most one request every 3 seconds


def fetch(query, max_records=MAX_PER_TOPIC):
    q = urllib.parse.urlencode({"search_query": query, "sortBy": "submittedDate",
                                "sortOrder": "descending", "max_results": max_records})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "ghost-signal/0.1 (Kiroween 2026)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return ET.fromstring(r.read()).findall("a:entry", NS)


def to_row(entry, topic, collected_at):
    def t(tag):
        return " ".join((entry.findtext(f"a:{tag}", "", NS) or "").split())
    url = t("id")
    if not url.startswith("http"):
        return None
    title, summary = t("title"), t("summary")
    return {
        "source": "arxiv", "source_type": "paper", "title": title, "url": url,
        "published_at": t("published") or None, "collected_at": collected_at,
        "raw_text": f"topic: {topic}\n{title}\n{summary}",
        "cleaned_text": f"{title}. {summary}", "language": "en",
    }


def collect(con, topics=TOPICS):
    now = datetime.now(timezone.utc).isoformat()
    total = 0
    for i, (topic, query) in enumerate(topics.items()):
        if i:
            time.sleep(RATE_LIMIT_S)
        try:
            entries = fetch(query)
        except Exception as e:
            print(f"[arxiv:{topic}] fetch failed: {e}")
            continue
        added = store(con, [r for e in entries if (r := to_row(e, topic, now))])
        total += added
        print(f"[arxiv:{topic}] fetched {len(entries)}, new {added}")
    return total
