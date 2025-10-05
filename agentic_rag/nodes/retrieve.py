# agentic_rag/nodes/retrieve.py
from typing import Dict, Any, List
from langchain_core.documents import Document
from ..config import TOP_K, MMR_K
from ..utils import compress_text, rrf_fuse


def _retrieve_vec_for_query(vec_source, query: str) -> List[Document]:
    """
    Works with either:
      - Chroma VectorStore (via .as_retriever(search_type='mmr', ...).invoke)
      - Any BaseRetriever-like object that exposes .invoke(query) (e.g., SupabaseANNRetriever)
    """
    # Chroma path (has .as_retriever)
    if hasattr(vec_source, "as_retriever"):
        retr = vec_source.as_retriever(
            search_type="mmr",
            search_kwargs={"k": MMR_K, "lambda_mult": 0.5}
        )
        return retr.invoke(query)

    # Generic retriever path (e.g., SupabaseANNRetriever)
    if hasattr(vec_source, "invoke"):
        return vec_source.invoke(query)

    return []  # unsupported vec_source


def retrieve(state: Dict[str, Any], vec_source, bm25_ret) -> Dict[str, Any]:
    queries: List[str] = state.get("queries") or [state.get("question", "")]
    pooled_vec: List[Document] = []
    pooled_bm25: List[Document] = []

    for q in queries:
        # Vector hits
        if vec_source is not None:
            pooled_vec.extend(_retrieve_vec_for_query(vec_source, q))
        # BM25 hits
        if bm25_ret is not None:
            pooled_bm25.extend(bm25_ret.invoke(q))

    # Fuse vector + BM25 pools (RRF), then compress for downstream nodes
    fused = rrf_fuse(pooled_vec, pooled_bm25, k=TOP_K)
    comp = [
        Document(page_content=compress_text(
            d.page_content), metadata=d.metadata)
        for d in fused
    ]
    return {**state, "docs": comp}
