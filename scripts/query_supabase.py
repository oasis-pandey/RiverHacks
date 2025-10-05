# scripts/query_supabase.py
# Query Supabase ANN via match_documents RPC using RP-compressed query vector.

import os
import numpy as np
from dotenv import load_dotenv
from joblib import load
from supabase import create_client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
RP_PATH = os.getenv("RP_PATH", "models/rp_3072to1024.joblib")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
RPC_NAME = os.getenv("SUPABASE_QUERY_NAME", "match_documents")


def l2norm(x: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(x)) + 1e-12
    return (x / n).astype(np.float32)


def search(q: str, k: int = 8, probes: int = 20):
    emb = GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL, google_api_key=GOOGLE_API_KEY)
    v_full = np.array(emb.embed_query(q), dtype=np.float32)
    v_full = l2norm(v_full)

    rp = load(RP_PATH)
    W = rp["W"].astype(np.float32)
    v_comp = l2norm(W @ v_full)  # 1024-d

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    def to_pylist(x):
        return x.astype(float).tolist()

    res = sb.rpc(
        RPC_NAME,
        {"query_embedding": to_pylist(
            v_comp), "match_count": k, "filter": {}, "probes": probes},
    ).execute()

    rows = res.data or []
    for i, r in enumerate(rows, 1):
        md = r.get("metadata") or {}
        title = md.get("title") or "(untitled)"
        url = md.get("url") or md.get("source") or ""
        sim = r.get("similarity", 0.0)
        print(f"[{i}] {title} — {url} (sim={sim:.3f})")
        content = r.get("content") or ""
        snippet = (content[:240] + "…") if len(content) > 240 else content
        print(snippet, "\n")


if __name__ == "__main__":
    # Example query
    search("Bion-M 1 görevinde erkek farelerin seçilme nedeni neydi?", k=8, probes=20)
