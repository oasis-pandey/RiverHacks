from typing import List, Optional, Literal
from pydantic import BaseModel, Field


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
    image: Optional[str] = None            # single primary thumbnail
    images: Optional[List[str]] = None     # all discovered images (if any)
    snippet: Optional[str] = None          # short excerpt
    type: Optional[str] = None             # e.g. "rag" | "web" (optional)
    rank: Optional[int] = None             # web rank (optional)


class AskResponse(BaseModel):
    """RAG answer with its supporting sources."""
    answer: str
    sources: List[SourceItem] = []


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


class SearchResponse(BaseModel):
    """Vector search response with ranked hits."""
    hits: List[SearchHit] = []


# =========================
# Hybrid (Web + RAG)
# =========================

class WebOptions(BaseModel):
    """
    Controls external search behavior (SerpAPI).
    Matches the UI payload under `web`.
    """
    google: bool = True          # include Google Web Search
    scholar: bool = True         # include Google Scholar
    scrape: bool = False         # scrape landing pages for text/images
    fetch_pdfs: bool = False     # download + parse open PDFs when available
    max_results: int = 3         # per engine (google/scholar)


class HybridAskRequest(BaseModel):
    """
    Hybrid request: send user question, plus RAG and Web knobs.

    - `k` and `probes` are accepted from UI and mapped to `rag_k` and `rag_probes`
      via field aliases for backward/forward compatibility.
    - `web` carries external search options (Google/Scholar/scrape/PDFs).
    """
    question: str
    rag_k: int = Field(6, alias="k", description="Top-k for vector search")
    rag_probes: int = Field(
        12, alias="probes", description="IVFFlat probes (pgvector)")
    web: WebOptions = Field(default_factory=WebOptions,
                            description="External search options")
    thread_id: Optional[str] = "hybrid"

    class Config:
        # allow either field names (rag_k) or aliases (k) in incoming JSON
        allow_population_by_field_name = True
        # ignore unexpected extra fields to avoid breaking older clients
        extra = "allow"


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

    # Visuals
    image: Optional[str] = None            # primary thumbnail (if any)
    images: Optional[List[str]] = None     # all images (if collected)
    favicon: Optional[str] = None          # site icon (if provided)


class HybridAskResponse(BaseModel):
    """Final synthesized answer with a flat list of all sources (web + scholar + rag)."""
    answer: str
    sources: List[HybridSource] = []
