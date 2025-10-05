from __future__ import annotations
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from .config import PERSIST_DIR, COLLECTION, RRF_K


def open_vectorstore(embeddings) -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )


def build_bm25_from_store(vs: Chroma) -> BM25Retriever:
    # Build BM25 from stored documents; if you persist raw docs elsewhere, load those instead.
    # returns { ids, documents, metadatas, embeddings? }
    raw = vs.get(include=["documents"])
    texts = raw.get("documents", [])
    bm25 = BM25Retriever.from_texts(texts)
    bm25.k = RRF_K
    return bm25
