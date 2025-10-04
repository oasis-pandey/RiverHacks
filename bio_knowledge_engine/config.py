"""
Configuration for API keys and environment variables.
"""

import os
from dotenv import load_dotenv

# Load variables from .env (optional, if you have one)
load_dotenv()

# Get the SERPAPI key from the environment
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not SERPAPI_KEY:
    print("⚠️  Warning: SERPAPI_KEY not found in environment.")
