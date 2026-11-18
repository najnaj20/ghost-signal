"""Run the collector once, or every N hours with --every N (FR-1.2)."""
import argparse
import time

from src.collector.gdelt import collect
from src.db import connect


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=float, help="repeat every N hours (PRD: about 4)")
    args = ap.parse_args()
    con = connect()
    while True:
        added = collect(con)
        n = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        print(f"new documents: {added}, total: {n}")
        if not args.every:
            break
        time.sleep(args.every * 3600)


if __name__ == "__main__":
    main()
