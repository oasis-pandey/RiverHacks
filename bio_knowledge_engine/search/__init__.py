""" Bio Knowledge Engine Search Module
 Author : Sinan Demir
 Date   : 10/04/2025
 Purpose: Initialize the search module and import necessary components.
"""

from .serpapi_client import (
    search_web_serpapi,
    search_scholar_serpapi,
    build_external_context,
    fetch_scholar_results,  # backward-compat
)

__all__ = [
    "search_web_serpapi",
    "search_scholar_serpapi",
    "build_external_context",
    "fetch_scholar_results",
]
