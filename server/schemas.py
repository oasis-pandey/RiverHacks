from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# =========================
# RAG-only (vector search)
# =========================

class AskRequest(BaseModel):
    """Simple chat/ask request for the RAG graph (agentic flow)."""
    question: str = Field(..., description="User question")
    thread_id: Optional[str] = "api"


class SourceItem(BaseModel):
    """Generic source descriptor used by pure RAG responses."""
    title: Optional[str] = None
    url: Optional[str] = None
    doc_id: Optional[str] = None
    similarity: Optional[float] = None

    # Optional visual/preview fields (handy for UI cards)
    # single primary thumbnail (URL string)
    image: Optional[str] = None
    images: Optional[List[str]] = None     # all discovered image URLs
    snippet: Optional[str] = None          # short excerpt
    type: Optional[str] = None             # e.g. "rag" | "web" (optional)
    rank: Optional[int] = None             # web rank (optional)


class AskResponse(BaseModel):
    """RAG answer with its supporting sources."""
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Direct vector search request (no synthesis)."""
    query: str
    k: int = 8
    probes: int = 20


class SearchHit(BaseModel):
    """Single hit from vector search."""
    title: Optional[str] = None
    url: Optional[str] = None
    doc_id: Optional[str] = None
    similarity: Optional[float] = None
    snippet: Optional[str] = None

    # Add image URL fields so /rag/search can return thumbnails from metadata
    image: Optional[str] = None
    images: Optional[List[str]] = None
    favicon: Optional[str] = None


class SearchResponse(BaseModel):
    """Vector search response with ranked hits."""
    hits: List[SearchHit] = Field(default_factory=list)


# =========================
# Hybrid (Web + RAG)
# =========================

class WebOptions(BaseModel):
    """
    Controls external search behavior (SerpAPI).
    This mirrors the UI payload under `web`.
    """
    google: bool = True          # include Google Web Search
    scholar: bool = True         # include Google Scholar
    scrape: bool = False         # scrape landing pages for text/images
    fetch_pdfs: bool = False     # download + parse open PDFs when available
    max_results: int = 3         # per engine (google/scholar)


class HybridAskRequest(BaseModel):
    """
    Hybrid request: user question + knobs for RAG and Web.

    - Accepts both aliases from old UI (`k`, `probes`) and explicit names
      (`rag_k`, `rag_probes`).
    - `web` carries external search options.
    """
    question: str
    rag_k: int = Field(6, alias="k", description="Top-k for vector search")
    rag_probes: int = Field(12, alias="probes",
                            description="IVFFlat probes (pgvector)")
    web: WebOptions = Field(default_factory=WebOptions,
                            description="External search options")
    thread_id: Optional[str] = "hybrid"

    # Pydantic v2 config
    model_config = ConfigDict(
        populate_by_name=True,  # allow population by field name when alias exists
        extra="allow",          # ignore unexpected extra fields from older clients
    )


class HybridSource(BaseModel):
    """
    Unified source item for hybrid responses.
    kind: "web" | "scholar" | "rag"
    """
    kind: Literal["web", "scholar", "rag"]
    title: Optional[str] = None
    url: Optional[str] = None
    doc_id: Optional[str] = None
    similarity: Optional[float] = None
    snippet: Optional[str] = None

    # Visuals (URLs only, no binaries)
    image: Optional[str] = None            # primary thumbnail URL (if any)
    images: Optional[List[str]] = None     # all image URLs (if collected)
    favicon: Optional[str] = None          # site icon URL (if provided)


class HybridAskResponse(BaseModel):
    """Final synthesized answer with a flat list of all sources (web + scholar + rag)."""
    answer: str
    sources: List[HybridSource] = Field(default_factory=list)
