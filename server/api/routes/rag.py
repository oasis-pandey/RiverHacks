from fastapi import APIRouter, Request, HTTPException
from typing import List, Tuple, Any, Optional
from server.schemas import (
    AskRequest, AskResponse, SourceItem,
    SearchRequest, SearchResponse, SearchHit
)

router = APIRouter(prefix="/rag", tags=["rag"])

# ---- image helpers ----------------------------------------------------------

IMG_KEYS = ("images", "figures", "thumbnails", "imgs", "pics")
URL_KEYS = ("src", "url", "href", "image", "link", "data-src", "data-original")


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _pick_url(obj: Any) -> Optional[str]:
    """Extract a single URL from a str OR a dict with common keys."""
    if isinstance(obj, str):
        return obj.strip() or None
    if isinstance(obj, dict):
        for k in URL_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _is_probably_image(u: str) -> bool:
    """Loosely filter to likely-real images (not icons/logos/svgs)."""
    s = (u or "").lower().strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        return False
    exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
    if any(s.endswith(e) for e in exts):
        return True
    # sometimes figure endpoints lack extensions
    return (
        ("figure" in s) or
        ("fig" in s) or
        ("images" in s and "logo" not in s and "icon" not in s and ".svg" not in s)
    )


def _extract_image_fields(md: dict) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Normalize image fields from metadata.
    Returns (image, images).
    """
    # 1) direct single fields
    single: Optional[str] = None
    for k in ("image", "thumbnail"):
        v = md.get(k)
        u = _pick_url(v)
        if u and _is_probably_image(u):
            single = u
            break

    # 2) lists under common keys
    pool: List[str] = []
    for k in IMG_KEYS:
        if k in md and md[k]:
            for item in _ensure_list(md[k]):
                u = _pick_url(item)
                if u and _is_probably_image(u):
                    pool.append(u)

    # 3) fallback: if single empty but pool has items
    if not single and pool:
        single = pool[0]

    # dedup pool while keeping order
    if pool:
        seen = set()
        dedup = []
        for u in pool:
            if u not in seen:
                seen.add(u)
                dedup.append(u)
        pool = dedup

    return single, (pool or None)


def _excerpt(text: str, limit: int = 240) -> str:
    if not text:
        return ""
    return (text[:limit] + "…") if len(text) > limit else text


# ---- sources extractor ------------------------------------------------------

def _extract_sources(state) -> List[SourceItem]:
    docs = state.get("graded_docs") or state.get("docs") or []
    items: List[SourceItem] = []
    for d in docs:
        md = getattr(d, "metadata", None) or {}
        img, imgs = _extract_image_fields(md)
        items.append(
            SourceItem(
                title=md.get("title"),
                url=md.get("url") or md.get("source"),
                doc_id=md.get("doc_id"),
                similarity=md.get("similarity"),
                snippet=_excerpt(getattr(d, "page_content", "")),
                type="rag",
                image=img,
                images=imgs,
            )
        )
    return items


# ---- routes ----------------------------------------------------------------

@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request):
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(500, "Graph not initialized")

    state = graph.invoke(req.question, thread_id=req.thread_id or "api")
    answer = state.get("draft", "") or "(no answer)"
    sources = _extract_sources(state)
    return AskResponse(answer=answer, sources=sources)


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, request: Request):
    graph = request.app.state.graph
    if graph is None or not hasattr(graph, "supa") or graph.supa is None:
        raise HTTPException(500, "Supabase retriever not initialized")

    docs = graph.supa.invoke(req.query, k=req.k, probes=req.probes)

    hits: List[SearchHit] = []
    for d in docs:
        md = d.metadata or {}
        img, imgs = _extract_image_fields(md)
        hits.append(
            SearchHit(
                title=md.get("title"),
                url=md.get("url") or md.get("source"),
                doc_id=md.get("doc_id"),
                similarity=md.get("similarity"),
                snippet=_excerpt(d.page_content or ""),
                # requires schema fields below ⬇
                image=img,
                images=imgs,
            )
        )
    return SearchResponse(hits=hits)
