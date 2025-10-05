from __future__ import annotations
import re
from typing import List, Dict
from langchain_core.documents import Document
from .config import MAX_CTX_CHARS


def scrub_think(text: str) -> str:
    t = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
    t = re.sub(r"<think>.*", "", t, flags=re.DOTALL)
    return t.strip()


def cite_block(docs: List[Document]) -> str:
    uniq = []
    seen = set()
    for d in docs:
        key = (d.metadata.get("title"), d.metadata.get(
            "url"), d.metadata.get("source"))
        if key not in seen:
            seen.add(key)
            title = d.metadata.get("title") or "(untitled)"
            url = d.metadata.get("url") or d.metadata.get("source") or ""
            uniq.append(f"- {title} — {url}")
    return "\n".join(uniq) if uniq else "- (no sources)"


def compress_text(text: str) -> str:
    return text[:MAX_CTX_CHARS] + ("\n\n[truncated]" if len(text) > MAX_CTX_CHARS else "")


def rrf_fuse(vector_hits: List[Document], bm25_hits: List[Document], k: int = 8) -> List[Document]:
    rank: Dict[str, float] = {}

    def add(list_docs: List[Document], weight: float = 1.0):
        for idx, d in enumerate(list_docs, start=1):
            key = (d.page_content[:200] +
                   (d.metadata.get("source") or "")).strip()
            score = weight * (1.0 / (60 + idx))
            rank[key] = rank.get(key, 0.0) + score

        add(vector_hits, weight=1.0)
        add(bm25_hits, weight=0.8)

    first_map = {}
    for d in vector_hits + bm25_hits:
        key = (d.page_content[:200] + (d.metadata.get("source") or "")).strip()
        if key not in first_map:
            first_map[key] = d

    fused = sorted(rank.items(), key=lambda x: x[1], reverse=True)[:k]
    return [first_map[k] for k, _ in fused]
