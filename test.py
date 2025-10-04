import json
import re
from bio_knowledge_engine.search import fetch_scholar_results

import json
import re

def build_structured_json(papers):
    structured = []
    for paper in papers:
        pdf_text = paper.get("pdf_text")

        # 🧱 Defensive fallback if PDF extraction failed
        if not isinstance(pdf_text, str):
            pdf_text = ""  # ensures re.split() never sees None

        # Split text into readable paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', pdf_text) if p.strip()]

        structured.append({
            "row": {
                "Title": paper.get("title", "Unknown Title"),
                "Link": paper.get("link", "")
            },
            "scrape": {
                "url": paper.get("link", ""),
                "title": paper.get("title", "Untitled"),
                "authors": paper.get("publication_info", ""),
                "abstract": paper.get("snippet", ""),
                "paragraphs": paragraphs
            }
        })

    print(f"✅ Structured {len(structured)} papers successfully.")
    return structured


if __name__ == "__main__":
    results = fetch_scholar_results("microgravity biology", 3)
    structured_data = build_structured_json(results)
    with open("data/json/microgravity_structured.json", "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=4, ensure_ascii=False)
