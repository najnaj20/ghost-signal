"""Run all collectors once, or every N hours with --every N (FR-1.2)."""
import argparse
import time

from src.collector import arxiv, gdelt, hn
from src.db import connect

SOURCES = {"gdelt": gdelt.collect, "arxiv": arxiv.collect, "hn": hn.collect}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=float, help="repeat every N hours (PRD: about 4)")
    ap.add_argument("--only", choices=SOURCES, help="run one source")
    args = ap.parse_args()
    con = connect()
    while True:
        added = sum(f(con) for name, f in SOURCES.items() if args.only in (None, name))
        n = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        print(f"new documents: {added}, total: {n}")
        if not args.every:
            break
        time.sleep(args.every * 3600)


if __name__ == "__main__":
    main()
