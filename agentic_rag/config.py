import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).resolve().parent.parent

# --- Models ---
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
GEN_MODEL = os.getenv("GEN_MODEL",   "gemini-2.5-flash")

# --- RAG params ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
HYDE_EXPS = int(os.getenv("HYDE_EXPS", "3"))
TOP_K = int(os.getenv("TOP_K", "8"))
MMR_K = int(os.getenv("MMR_K", "6"))
MAX_CTX_CHARS = int(os.getenv("MAX_CTX_CHARS", "14000"))
RRF_K = int(os.getenv("RRF_K", "20"))
LOOP_MAX = int(os.getenv("LOOP_MAX", "2"))
STOP_TOKENS = ["</think>"]

# --- Corpus ---
JSON_PATH = os.getenv("JSON_PATH",   str(BASE / "data" / "corpus"))

# --- (Option C) compressor paths ---
# If you're using Random Projection (RP):
RP_PATH = os.getenv("RP_PATH", str(BASE / "models" / "rp_3072to1024.joblib"))
# (If later you switch to PCA, you may also keep:)
PCA_PATH = os.getenv("PCA_PATH", str(
    BASE / "models" / "pca_3072to1024.joblib"))

# --- Supabase (pgvector) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Prefer Service Role for indexing; fall back to anon for read-only:
SUPABASE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "documents")
# RPC function name used by the retriever
SUPABASE_QUERY = os.getenv("SUPABASE_QUERY_NAME", "match_documents")

# --- Chroma (if you still keep it around as fallback) ---
PERSIST_DIR = os.getenv("PERSIST_DIR", str(BASE / "chroma_python_docs"))
COLLECTION = os.getenv("COLLECTION",  "python_docs")
