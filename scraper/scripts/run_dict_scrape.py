#!/usr/bin/env python3
"""Run scraper against a JSON dictionary of title -> url pairs."""
import argparse
import json
from pathlib import Path
from scraper_core import scrape_rows, write_json


def dict_to_rows(d):
    rows = []
    for title, url in d.items():
        rows.append({"Title": title, "url": url})
    return rows


def main():
    parser = argparse.ArgumentParser(description="Scrape from a JSON dict of title->url")
    parser.add_argument("--input", required=True, help="Input JSON file with title->url mapping")
    parser.add_argument("--output", required=True, help="Output JSON file to write results")
    parser.add_argument("--limit", type=int, help="Limit number of entries to process")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI refinement step for faster runs")

    args = parser.parse_args()

    path = Path(args.input)
    data = json.loads(path.read_text(encoding="utf-8"))

    rows = dict_to_rows(data)
    if args.limit:
        rows = rows[: args.limit]

    print(f"Scraping {len(rows)} entries from {args.input} (delay={args.delay}, ai_refine={not args.no_ai})")

    results = scrape_rows(rows, delay=args.delay, refine_ai=not args.no_ai)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(results, str(out_path))

    print(f"Wrote results to {out_path}")


if __name__ == "__main__":
    main()
