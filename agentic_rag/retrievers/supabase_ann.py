# agentic_rag/retrievers/supabase_ann.py
from typing import List, Optional, Dict, Any
import os
import json
import numpy as np
from joblib import load
from supabase import create_client
from langchain_core.documents import Document


class SupabaseANNRetriever:
    """
    Minimal ANN retriever over Supabase pgvector.

    - If rp_path is provided and dimensions match, applies random projection (e.g., 3072 -> 1024).
      Otherwise uses the embedding vector as-is (e.g., Ollama 1024).
    - k/probes can be overridden per-call.
    - Oversampling helps us deduplicate chunk-level hits into unique article-level hits.
    """

    def __init__(
        self,
        url: str,
        key: str,
        rpc_name: str,
        rp_path: Optional[str],
        embedder,                 # any Embeddings with .embed_query()
        k: int = 8,
        probes: int = 20,
    ):
        self.client = create_client(url, key)
        self.rpc_name = rpc_name
        self.embedder = embedder
        self.k = k
        self.probes = probes

        # Optional random-projection matrix (W)
        self.W: Optional[np.ndarray] = None
        self._W_in_dim: Optional[int] = None
        if rp_path and os.path.exists(rp_path):
            rp = load(rp_path)  # expected shape like {"W": (1024, 3072)}
            W = rp.get("W", None)
            if W is not None:
                W = np.asarray(W, dtype=np.float32)
                self.W = W
                self._W_in_dim = W.shape[1]  # expected input dim (e.g., 3072)

    # ---------- helpers ----------

    @staticmethod
    def _l2(x: np.ndarray) -> np.ndarray:
        n = float(np.linalg.norm(x)) + 1e-12
        return (x / n).astype(np.float32)

    def _maybe_project(self, v: np.ndarray) -> np.ndarray:
        """Apply RP only if W exists and input dims match; otherwise pass-through."""
        if self.W is None:
            return v
        if self._W_in_dim is not None and v.size != self._W_in_dim:
            # Dimension mismatch (e.g., embedder=1024-d, W expects 3072-d)
            return v
        return self._l2(self.W @ v)

    @staticmethod
    def _normalize_images(imgs: Any) -> Optional[List[str]]:
        """
        Accepts:
          - list[str] (already URLs)
          - list[dict] with 'src' or 'url'
        Returns a de-duplicated list[str] (URLs) or None.
        """
        if not imgs:
            return None
        out: List[str] = []
        if isinstance(imgs, list):
            for it in imgs:
                if isinstance(it, str):
                    u = it.strip()
                    if u:
                        out.append(u)
                elif isinstance(it, dict):
                    u = (it.get("src") or it.get("url") or "").strip()
                    if u:
                        out.append(u)
        # dedup while preserving order
        seen = set()
        uniq: List[str] = []
        for u in out:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq or None

    @staticmethod
    def _parse_md(md_raw: Any, row_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Robust metadata parser:
          - Accepts dict or JSON string
          - Pulls images from md['images'] or md['scrape']['images']
          - Picks a primary image if missing
          - Fills 'url' from md/url/source/link/row_url fallback
        """
        md: Dict[str, Any] = {}
        if md_raw is None:
            pass
        elif isinstance(md_raw, dict):
            md = dict(md_raw)  # shallow copy
        elif isinstance(md_raw, str):
            try:
                parsed = json.loads(md_raw)
                if isinstance(parsed, dict):
                    md = parsed
            except Exception:
                md = {}
        else:
            md = {}

        # images from top-level or nested scrape
        images = md.get("images")
        if not images:
            scrape = md.get("scrape")
            if isinstance(scrape, dict):
                images = scrape.get("images")

        images = SupabaseANNRetriever._normalize_images(images)
        if images:
            md["images"] = images
            md.setdefault("image", images[0])

        # normalize url
        url = (
            md.get("url")
            or md.get("source")
            or md.get("link")
            or row_url
        )
        if url:
            md["url"] = url

        return md

    @staticmethod
    def _dedup_best(docs: List[Document], topk: int) -> List[Document]:
        """
        Deduplicate by a stable priority key and keep the highest-similarity doc:
          priority: doi -> url -> source -> title -> doc_id
        """
        best: Dict[str, Document] = {}
        for d in docs:
            md = d.metadata or {}
            key = md.get("doi") or md.get("url") or md.get(
                "source") or md.get("title") or md.get("doc_id")
            sim = float(md.get("similarity") or 0.0)
            prev = best.get(key)
            if prev is None or sim > float((prev.metadata or {}).get("similarity") or 0.0):
                best[key] = d
        uniq = list(best.values())
        uniq.sort(key=lambda x: float(
            (x.metadata or {}).get("similarity") or 0.0), reverse=True)
        return uniq[:topk]

    # ---------- main entry ----------

    def invoke(
        self,
        query: str,
        k: Optional[int] = None,
        probes: Optional[int] = None,
        oversample: int = 6,
        extra_filter: Optional[dict] = None,
    ) -> List[Document]:
        # 1) Embed
        v = np.asarray(self.embedder.embed_query(query), dtype=np.float32)
        v = self._l2(v)

        # 2) Optional random projection
        v = self._maybe_project(v)

        # 3) RPC call (oversample to improve dedup)
        eff_k = int(k or self.k)
        eff_probes = int(probes or self.probes)
        match_count = min(max(eff_k * oversample, eff_k),
                          100)  # safe upper bound

        payload = {
            "query_embedding": v.astype(float).tolist(),
            "match_count": match_count,
            "probes": eff_probes,
        }
        if extra_filter:
            payload["filter"] = extra_filter

        res = self.client.rpc(self.rpc_name, payload).execute()
        rows = res.data or []

        # 4) Rows -> Documents (robust metadata; carry images/url/similarity/doc_id)
        docs: List[Document] = []
        for r in rows:
            row_url = r.get("url")
            md = self._parse_md(r.get("metadata"), row_url=row_url)
            md.update({
                "doc_id": r.get("doc_id"),
                "similarity": r.get("similarity"),
            })
            content = r.get("content") or ""
            docs.append(Document(page_content=content, metadata=md))

        # 5) Deduplicate to article-level
        return self._dedup_best(docs, topk=eff_k)
