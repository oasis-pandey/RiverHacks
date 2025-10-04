#!/usr/bin/env python3

import argparse
from pathlib import Path
from scraper_core import read_csv_from_url, scrape_rows, write_json

def main():
    parser = argparse.ArgumentParser(description="NASA Publication Scraper")
    parser.add_argument("--csv-url", required=True, help="CSV URL to scrape")
    parser.add_argument("--count", type=int, help="Number of entries to scrape")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests")
    
    args = parser.parse_args()
    
    print(f"Starting scrape from: {args.csv_url}")
    csv_data = read_csv_from_url(args.csv_url)
    
    if args.count:
        csv_data = csv_data[:args.count]
    
    print(f"Processing {len(csv_data)} entries")
    results = scrape_rows(csv_data, delay=args.delay)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(results, str(output_path))
    
    print(f"Complete! Scraped {len(results)} publications")

if __name__ == "__main__":
    main()
