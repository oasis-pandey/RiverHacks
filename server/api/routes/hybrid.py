from fastapi import APIRouter, Request, HTTPException
from typing import List, Tuple, Any, Optional

from server.schemas import HybridAskRequest, HybridAskResponse, HybridSource
from bio_knowledge_engine.search.serpapi_client import build_external_context

router = APIRouter(prefix="/hybrid", tags=["hybrid"])

# ---- image helpers (RAG metadata -> image, images) --------------------------

IMG_KEYS = ("images", "figures", "thumbnails", "imgs", "pics")
URL_KEYS = (
    "src", "url", "href", "image", "link",
    "data-src", "data-original", "image_url", "thumbnail_url"
)


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _pick_url(obj: Any) -> Optional[str]:
    """Extract a URL from str or dict-like objects with common keys."""
    if isinstance(obj, str):
        s = obj.strip()
        return s or None
    if isinstance(obj, dict):
        for k in URL_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _is_probably_image(u: str) -> bool:
    """Heuristic: prefer real images; avoid icons/logos/svg."""
    s = (u or "").lower().strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        return False
    exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
    if any(s.endswith(e) for e in exts):
        return True
    # some figure endpoints have no extension
    return (
        ("figure" in s) or
        ("fig" in s) or
        ("images" in s and "logo" not in s and "icon" not in s and ".svg" not in s)
    )


def _extract_image_fields(md: dict) -> Tuple[Optional[str], Optional[List[str]]]:
    """Return normalized (image, images) from RAG metadata dict."""
    # 1) direct single candidates
    single: Optional[str] = None
    for k in ("image", "thumbnail"):
        v = md.get(k)
        u = _pick_url(v)
        if u and _is_probably_image(u):
            single = u
            break

    # 2) aggregate lists from common keys
    pool: List[str] = []
    for k in IMG_KEYS:
        if k in md and md[k]:
            for item in _ensure_list(md[k]):
                u = _pick_url(item)
                if u and _is_probably_image(u):
                    pool.append(u)

    # 3) fallback single from pool
    if not single and pool:
        single = pool[0]

    # 4) dedup pool preserving order
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


# ---- dual-query prompt ------------------------------------------------------

def make_dual_queries(llm, question: str) -> Tuple[List[str], List[str]]:
    """
    Generate two query sets:
      - web_queries: broader keyword queries for Google/Scholar
      - rag_queries: concise semantic queries for vector search
    Returns (web_queries, rag_queries).
    """
    sys = (
        "You split a user question into two sets of queries:\n"
        "1) web_queries: broad, keyword-rich, suitable for Google Search/Scholar\n"
        "2) rag_queries: concise semantic queries for vector search\n"
        "Return JSON with fields: web_queries, rag_queries."
    )
    user = f"Question: {question}"
    try:
        msg = [{"role": "system", "content": sys},
               {"role": "user", "content": user}]
        resp = llm.invoke(msg)
        txt = resp.content if hasattr(resp, "content") else str(resp)
    except Exception:
        return [question], [question]

    import json
    import re
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return [question], [question]
    try:
        data = json.loads(m.group(0))
        web_q = data.get("web_queries") or [question]
        rag_q = data.get("rag_queries") or [question]
        web_q = [q.strip() for q in web_q if isinstance(q, str) and q.strip()]
        rag_q = [q.strip() for q in rag_q if isinstance(q, str) and q.strip()]
        return web_q or [question], rag_q or [question]
    except Exception:
        return [question], [question]


# ---- synthesis prompt -------------------------------------------------------

def build_synthesis_prompt(question: str, web_items: List[dict], rag_docs: List):
    def short(t, n=300):
        if not t:
            return ""
        return (t[:n] + "…") if len(t) > n else t

    lines: List[str] = []
    lines.append("You are a careful researcher. Synthesize the answer.\n")
    lines.append(f"User question:\n{question}\n")

    # Web/Scholar block
    lines.append("\n[External search context]")
    for i, it in enumerate(web_items, 1):
        lines.append(f"- ({i}) {it.get('title') or it.get('url')}")
        if it.get("snippet"):
            lines.append(f"  snippet: {short(it['snippet'], 300)}")
        if it.get("text"):  # scraped or PDF text if available
            lines.append(f"  text: {short(it['text'], 600)}")
        lines.append(f"  url: {it.get('url')}")

    # RAG block
    lines.append("\n[RAG context]")
    for j, d in enumerate(rag_docs, 1):
        md = getattr(d, "metadata", {}) or {}
        title = md.get("title") or md.get("source")
        url = md.get("url") or md.get("source")
        lines.append(f"- [R{j}] {title} | {url}")
        lines.append(
            f"  excerpt: {short(getattr(d, 'page_content', ''), 600)}")

    lines.append(
        "\nInstructions:\n"
        "- Combine both contexts. Prefer peer-reviewed & higher quality when conflicting.\n"
        "- Be specific. Include key numbers if present.\n"
        "- Cite inline like [R1], [W2] where R=RAG item index, W=Web/Scholar item index.\n"
        "- If uncertain, state limitations.\n"
    )
    return "\n".join(lines)


# ---- route ------------------------------------------------------------------

@router.post("/ask", response_model=HybridAskResponse)
def ask_hybrid(req: HybridAskRequest, request: Request):
    app = request.app
    graph = app.state.graph
    if graph is None:
        raise HTTPException(500, "Graph not initialized")

    # 1) Create query sets
    web_queries, rag_queries = make_dual_queries(graph.llm, req.question)

    # 2) SerpAPI (Google + Scholar). We keep images for web empty; RAG will supply images.
    try:
        web_ctx = build_external_context(
            query=" OR ".join(web_queries),
            k_web=req.web_k,
            k_scholar=req.scholar_k,
            fetch_pdfs=req.fetch_pdfs,
            scrape_links=True,  # turn off if timeouts
        )
    except Exception:
        web_ctx = {"web": [], "scholar": []}

    web_items = (web_ctx.get("web") or []) + (web_ctx.get("scholar") or [])

    # 3) RAG retrieval
    rag_q = " ".join(rag_queries) if rag_queries else req.question
    try:
        rag_docs = graph.supa.invoke(rag_q, k=req.rag_k)
    except Exception:
        rag_docs = []

    # 4) Synthesis via LLM
    prompt = build_synthesis_prompt(req.question, web_items, rag_docs)
    try:
        out = graph.llm.invoke(prompt)
        answer = out.content if hasattr(out, "content") else str(out)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")

    # 5) Sources payload (web/scholar first, then rag with images)
    sources: List[HybridSource] = []

    # web/scholar
    for it in web_items:
        sources.append(
            HybridSource(
                kind="scholar" if it.get("source") == "scholar" else "web",
                title=it.get("title"),
                url=it.get("url"),
                snippet=it.get("snippet"),
                # images intentionally omitted for web
            )
        )

    # rag (with images)
    for d in rag_docs:
        md = getattr(d, "metadata", {}) or {}
        img, imgs = _extract_image_fields(md)
        sources.append(
            HybridSource(
                kind="rag",
                title=md.get("title"),
                url=md.get("url") or md.get("source"),
                doc_id=md.get("doc_id"),
                similarity=md.get("similarity"),
                snippet=_excerpt(getattr(d, "page_content", "")),
                image=img,
                images=imgs,
            )
        )

    return HybridAskResponse(answer=answer, sources=sources)
