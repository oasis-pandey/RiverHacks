
import re
import fitz  # PyMuPDF
import requests
from serpapi import GoogleSearch
from bio_knowledge_engine.config import SERPAPI_KEY


# ===============================
# 🔍 Fetching from Google Scholar
# ===============================

def fetch_scholar_results(query: str, num_results: int = 5):
    """
    Fetches academic papers from Google Scholar using SerpAPI.

    Args:
        query (str): Search term, e.g., "cell growth in microgravity".
        num_results (int): Number of results to fetch (default=5).

    Returns:
        list[dict]: A list of dictionaries containing:
            - title
            - link
            - snippet
            - publication_info
            - pdf_text (if available)
    """
    if not SERPAPI_KEY:
        raise ValueError("Missing SERPAPI_KEY. Set it as an environment variable first.")

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

        # Try extracting PDF if resources available
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


# ===============================
# 📄 PDF Download & Text Extraction
# ===============================

def extract_text_from_pdf(pdf_url: str):
    """
    Download and extract clean, continuous text from an open-access PDF.
    Rebuilds proper paragraphs instead of page or line breaks.
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

        # 🧹 Step 1: merge broken lines inside paragraphs
        full_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', full_text)

        # 🧱 Step 2: normalize paragraph breaks
        full_text = re.sub(r'\n{2,}', '\n\n', full_text)

        # 🧼 Step 3: remove extra spaces
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # 🧩 Step 4: split into paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text) if len(p.strip()) > 50]

        # Return as one string and also list of paragraphs
        return "\n\n".join(paragraphs)

    except requests.exceptions.RequestException as e:
        print(f"⚠️ PDF request failed for {pdf_url}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Could not extract PDF from {pdf_url}: {e}")
        return None
    


# ===============================
# 🧹 Helper: Clean Text Formatting
# ===============================

def clean_pdf_text(raw_text: str) -> str:
    """
    Cleans raw PDF text while keeping paragraph and page structure.

    Args:
        raw_text (str): Unformatted text from a PDF page.

    Returns:
        str: Clean, human-readable text.
    """
    if not raw_text or not raw_text.strip():
        return ""

    # Merge line breaks intelligently:
    # 1. Replace single newlines within sentences with a space.
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)

    # 2. Keep paragraph breaks (two or more newlines).
    text = re.sub(r'\n{2,}', '\n\n', text)

    # 3. Normalize spacing and trim.
    text = re.sub(r'\s+', ' ', text).strip()

    return text