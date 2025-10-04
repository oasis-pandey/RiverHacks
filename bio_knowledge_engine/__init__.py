"""
bio_knowledge_engine
--------------------
A package for retrieving biology-related research papers from Google Scholar via SerpAPI.
"""

__version__ = "0.1.0"
__author__ = "Sinan"

# Optional: expose main functionality at the top level
from .search.serpapi_client import fetch_scholar_results
