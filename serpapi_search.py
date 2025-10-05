"""
SerpAPI integration for Google Scholar searches.
Adapted from your original serpapi_client.py
"""
import re
import fitz  
import requests
from serpapi import GoogleSearch
import os

#SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SERPAPI_KEY = '13dffb7b66530a24e779e9f2bb5d0f8d7217d07b33790de152d1819a95af9486'


def fetch_scholar_results(query: str, num_results: int = 5):
    """
    Fetches academic papers from Google Scholar using SerpAPI.
    """
    if not SERPAPI_KEY:
        raise ValueError("Missing SERPAPI_KEY environment variable")

    params = {
        "engine": "google_scholar",
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_KEY
    }

    print(f"🔎 Searching Google Scholar for: '{query}' ...")

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
    except Exception as e:
        print(f"❌ SerpAPI request failed: {e}")
        return []

    papers = []
    for r in organic_results:
        title = r.get("title")
        link = r.get("link")
        snippet = r.get("snippet", "")
        publication_info = r.get("publication_info", {}).get("summary", "")
        pdf_text = None

        # Try extracting PDF if available
        for res in r.get("resources", []):
            if res.get("file_format") == "PDF":
                pdf_link = res.get("link")
                pdf_text = extract_text_from_pdf(pdf_link)
                break

        papers.append({
            "title": title,
            "link": link,
            "snippet": snippet,
            "publication_info": publication_info,
            "pdf_text": pdf_text
        })

    print(f"✅ Retrieved {len(papers)} papers.")
    return papers


def extract_text_from_pdf(pdf_url: str):
    """
    Download and extract text from PDF.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(pdf_url, headers=headers, timeout=15)
        response.raise_for_status()

        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        full_text = ""
        with fitz.open("temp.pdf") as doc:
            for page in doc:
                full_text += page.get_text("text") + "\n\n"

        # Clean text
        full_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', full_text)
        full_text = re.sub(r'\n{2,}', '\n\n', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text) if len(p.strip()) > 50]

        return "\n\n".join(paragraphs)

    except Exception as e:
        print(f"⚠️ Could not extract PDF from {pdf_url}: {e}")
        return None


def build_structured_response(papers):
    """
    Build structured JSON response from papers.
    """
    structured = []
    for paper in papers:
        pdf_text = paper.get("pdf_text")

        if not isinstance(pdf_text, str):
            pdf_text = ""

        paragraphs = [p.strip() for p in re.split(r'\n{2,}', pdf_text) if p.strip()]

        structured.append({
            "title": paper.get("title", "Unknown Title"),
            "link": paper.get("link", ""),
            "snippet": paper.get("snippet", ""),
            "authors": paper.get("publication_info", ""),
            "paragraphs": paragraphs
        })

    return structured
