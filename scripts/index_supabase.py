# scripts/index_supabase.py
# Ingest JSON corpus into Supabase.
# Default: local Ollama embeddings (mxbai-embed-large, 1024-d) -> no RP/PCA needed.
# Optional: Gemini (3072-d) + Random Projection to 1024 if EMBED_BACKEND=gemini.
#
# - Loads JSON via our loader (keeps image URLs in metadata; captions in text)
# - Chunks text
# - Embeds (Ollama OR Gemini)
# - (If Gemini) compresses to 1024 via RP (sklearn or {"W":...})
# - L2-normalizes
# - Upserts batched rows into Supabase

import os
import hashlib
from typing import List, Dict, Any, Tuple

import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm
from supabase import create_client

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Backends (instantiate at runtime only)
from langchain_community.embeddings import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Our utils
from agentic_rag.ingest.loaders import load_ncbi_json_docs

# Optional RP loader (only used if EMBED_BACKEND=gemini)
try:
    from joblib import load as joblib_load
except Exception:
    joblib_load = None

load_dotenv()

# ---------- ENV ----------
EMBED_BACKEND = os.getenv(
    "EMBED_BACKEND", "ollama").lower()     # 'ollama' | 'gemini'

# Ollama
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Gemini (only if you insist)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")  # 3072-d
# needed for gemini path
RP_PATH = os.getenv("RP_PATH", "models/rp_3072to1024.joblib")

# Path can be a single file or a directory with *.json
JSON_PATH = os.getenv("JSON_PATH", "data/corpus")

# Supabase (use the service role key for server-side ingest)
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TABLE = os.getenv("SUPABASE_TABLE", "documents")

# Chunking & batching
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))

# Optional slicing for huge corpora
INDEX_LIMIT = int(os.getenv("INDEX_LIMIT", "0"))   # 0 => no cap
INDEX_START_OFFSET = int(os.getenv("INDEX_START_OFFSET", "0"))


# ---------- HELPERS ----------
def l2norm(x: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(x)) + 1e-12
    return (x / n).astype(np.float32)


def pylist(x: np.ndarray) -> List[float]:
    return [float(v) for v in np.asarray(x).ravel().tolist()]


def stable_doc_id(md: Dict[str, Any], content: str, chunk_idx: int) -> str:
    base = md.get("doc_id") or f"{md.get('url', '')}|{md.get('title', '')}"
    key = f"{base}|{chunk_idx}|{len(content)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def load_rp(path: str) -> Tuple[str, Any]:
    """Load RP either as sklearn transformer (with .transform) or dict with 'W'."""
    if joblib_load is None:
        raise RuntimeError(
            "joblib not available but RP_PATH is required for gemini backend.")
    obj = joblib_load(path)
    if hasattr(obj, "transform"):
        return ("sklearn", obj)
    if isinstance(obj, dict) and "W" in obj:
        W = np.asarray(obj["W"]).astype(np.float32)  # (1024, 3072)
        return ("matrix", W)
    raise RuntimeError(
        "Unsupported RP joblib format. Expect sklearn RP or {'W': ...} dict.")


def rp_project(vec3072: np.ndarray, rp_kind: str, rp_obj) -> np.ndarray:
    if rp_kind == "sklearn":
        out = rp_obj.transform([vec3072])[0]
        return np.asarray(out, dtype=np.float32)
    elif rp_kind == "matrix":
        W = rp_obj  # (1024, 3072)
        return (W @ vec3072.astype(np.float32))
    else:
        raise RuntimeError("Unknown RP kind")


def choose_embedder():
    """Return (backend, embedder, out_dim, note)."""
    if EMBED_BACKEND == "ollama":
        emb = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL,
                               base_url=OLLAMA_BASE_URL)
        dim = 1024  # mxbai-embed-large
        return ("ollama", emb, dim, f"ollama:{OLLAMA_EMBED_MODEL}")
    elif EMBED_BACKEND == "gemini":
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY missing but EMBED_BACKEND=gemini")
        emb = GoogleGenerativeAIEmbeddings(
            model=EMBED_MODEL, google_api_key=GOOGLE_API_KEY)
        dim = 3072  # will be RP-compressed to 1024
        return ("gemini", emb, dim, f"gemini:{EMBED_MODEL}")
    else:
        raise RuntimeError(f"Unknown EMBED_BACKEND={EMBED_BACKEND}")


# ---------- MAIN ----------
def main():
    # 1) Load docs
    docs = load_ncbi_json_docs(JSON_PATH)
    if not docs:
        raise SystemExit(f"No JSON docs found under: {JSON_PATH}")

    # 2) Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)

    if INDEX_LIMIT > 0:
        chunks = chunks[INDEX_START_OFFSET: INDEX_START_OFFSET + INDEX_LIMIT]

    print(f"Chunks: {len(chunks)}")

    # 3) Choose embedder
    backend, emb, in_dim, label = choose_embedder()
    print(f"[embeddings] backend={backend} ({label}), input_dim={in_dim}")

    # If Gemini path, prepare RP to 1024 so it matches DB vector(1024)
    rp_kind, rp_obj = (None, None)
    if backend == "gemini":
        rp_kind, rp_obj = load_rp(RP_PATH)
        print(f"[rp] loaded kind={rp_kind} from {RP_PATH} -> output_dim=1024")

    # 4) Supabase client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 5) Embed & upsert
    rows: List[Dict[str, Any]] = []
    for i, d in enumerate(tqdm(chunks, desc="Embed+upsert")):
        v = np.asarray(emb.embed_query(d.page_content), dtype=np.float32)
        v = l2norm(v)

        row: Dict[str, Any] = {
            "doc_id": stable_doc_id(d.metadata or {}, d.page_content, i),
            "content": d.page_content,
            "metadata": d.metadata or {},
        }

        if backend == "ollama":
            # already 1024-d
            row["embedding"] = pylist(v)         # vector(1024)
            # 'full_embedding' left absent on purpose
        else:
            # gemini 3072 -> RP -> 1024
            v_comp = l2norm(rp_project(v, rp_kind, rp_obj))
            row["embedding"] = pylist(v_comp)    # vector(1024)
            row["full_embedding"] = pylist(v)    # jsonb (optional column)

        rows.append(row)

        if len(rows) >= BATCH_SIZE:
            sb.table(TABLE).upsert(rows).execute()
            rows.clear()

    if rows:
        sb.table(TABLE).upsert(rows).execute()

    print("Done. Upserted into Supabase.")


if __name__ == "__main__":
    main()
