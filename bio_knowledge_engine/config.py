"""
Configuration for API keys and environment variables.
"""

import os
from dotenv import load_dotenv

# === SerpAPI ===
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_TIMEOUT = int(os.getenv("SERPAPI_TIMEOUT", "20"))
SERPAPI_GOOGLE_NUM = int(os.getenv("SERPAPI_GOOGLE_NUM", "5"))
SERPAPI_SCHOLAR_NUM = int(os.getenv("SERPAPI_SCHOLAR_NUM", "5"))

# === PDF limits ===
PDF_MAX_BYTES = int(os.getenv("PDF_MAX_BYTES", "25000000"))  # 25MB
PDF_MAX_PAGES = int(os.getenv("PDF_MAX_PAGES", "12"))

# === Web scraping (opsiyonel hızlı skim) ===
# web sonuçlarından ilk N URL’i hafifçe skim et
SCRAPE_TOP_N = int(os.getenv("SCRAPE_TOP_N", "2"))
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "15"))

# Load variables from .env (optional, if you have one)
load_dotenv()

# Get the SERPAPI key from the environment
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not SERPAPI_KEY:
    print("⚠️  Warning: SERPAPI_KEY not found in environment.")
