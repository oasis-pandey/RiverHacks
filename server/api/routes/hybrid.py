from fastapi import APIRouter, Request, HTTPException
from typing import List, Tuple, Any, Optional
from urllib.parse import urlparse

from server.schemas import HybridAskRequest, HybridAskResponse, HybridSource
from bio_knowledge_engine.search.serpapi_client import build_external_context

router = APIRouter(prefix="/hybrid", tags=["hybrid"])

# ---- RAG görsel link çıkarıcılar -------------------------------------------

IMG_KEYS = (
    "images", "figures", "thumbnails", "imgs", "pics",
    "figure_images", "preview_images",
)
SINGLE_IMG_KEYS = ("image", "thumbnail", "first_image", "cover", "cover_image")
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
    """Str veya dict içinden olası URL alanını çıkar."""
    if isinstance(obj, str):
        s = obj.strip()
        return s or None
    if isinstance(obj, dict):
        for k in URL_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _looks_like_visual(u: str) -> bool:
    """
    Görsel BENZERİ link mi?
    - Uzantılı gerçek görseller (.jpg/.png/.gif/.webp) => EVET
    - Uzantısız ama figure/fig/images/bin => EVET
    - Logo/icon/sprite/svg/static img => HAYIR
    """
    if not u:
        return False
    s = u.lower().strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        return False

    # bariz istenmeyenler
    if any(tok in s for tok in ("logo", "icon", "sprite", "favicon", "/static/img", ".svg")):
        return False

    if any(s.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return True

    if "/figure" in s or "/fig" in s or "/images" in s or "/bin/" in s:
        return True

    return False


def _ncbi_pmc_fallbacks(page_url: Optional[str]) -> List[str]:
    """
    NCBI/PMC makalelerinde görsel link bulunamadıysa makul fallback'ler.
    Bunlar HAM LİNKTİR (UI tıklanabilir gösterir).
    """
    if not page_url:
        return []
    try:
        u = page_url.strip().rstrip("/")
        host = urlparse(u).netloc.lower()
        if "ncbi.nlm.nih.gov" in host and "/pmc/articles/" in u:
            return [u + "/#figures", u + "/bin/", u + "/pdf"]
    except Exception:
        pass
    return []


def _dedup_keep_order(urls: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _extract_visual_links(md: dict) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Metadata'dan görsel benzeri linkleri topla ve normalize et.
    Dönüş: (image, images) -> string linkler (dosya değil).
    """
    prim: Optional[str] = None
    pool: List[str] = []

    # Tekil alanlar
    for k in SINGLE_IMG_KEYS:
        v = md.get(k)
        u = _pick_url(v)
        if u and _looks_like_visual(u):
            if not prim:
                prim = u
            pool.append(u)

    # Liste alanlar
    for k in IMG_KEYS:
        if k in md and md[k]:
            for item in _ensure_list(md[k]):
                u = _pick_url(item)
                if u and _looks_like_visual(u):
                    pool.append(u)

    # Hiç link yoksa: domain-özel fallback (PMC)
    if not pool:
        url = md.get("url") or md.get("source")
        pool.extend(_ncbi_pmc_fallbacks(url))

    pool = _dedup_keep_order(pool)
    if not prim and pool:
        prim = pool[0]

    return prim, (pool or None)


def _excerpt(text: str, limit: int = 240) -> str:
    if not text:
        return ""
    return (text[:limit] + "…") if len(text) > limit else text


# ---- dual-query prompt ------------------------------------------------------

def make_dual_queries(llm, question: str) -> Tuple[List[str], List[str]]:
    """
    web_queries: Google/Scholar için geniş anahtar kelimeli sorgular
    rag_queries: vektör arama için kısa semantik sorgular
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

    # Web/Scholar
    lines.append("\n[External search context]")
    for i, it in enumerate(web_items, 1):
        lines.append(f"- (W{i}) {it.get('title') or it.get('url')}")
        if it.get("snippet"):
            lines.append(f"  snippet: {short(it['snippet'], 300)}")
        if it.get("text"):
            lines.append(f"  text: {short(it['text'], 600)}")
        lines.append(f"  url: {it.get('url')}")

    # RAG
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

    # 1) Sorgu setleri
    web_queries, rag_queries = make_dual_queries(graph.llm, req.question)

    # 2) SerpAPI (Google + Scholar). WebOptions -> build_external_context
    web_opts = req.web
    try:
        web_ctx = build_external_context(
            query=" OR ".join(web_queries),
            # Eğer build_external_context 0 kabul etmiyorsa, implementasyonu
            # boş dönecek şekilde ayarlı olmalı. Aksi halde filtreyi aşağıda uygularız.
            k_web=web_opts.max_results if web_opts.google else 0,
            k_scholar=web_opts.max_results if web_opts.scholar else 0,
            fetch_pdfs=web_opts.fetch_pdfs,
            scrape_links=web_opts.scrape,
        )
    except Exception:
        web_ctx = {"web": [], "scholar": []}

    web_items = (web_ctx.get("web") or []) + (web_ctx.get("scholar") or [])

    # 3) RAG
    rag_q = " ".join(rag_queries) if rag_queries else req.question
    try:
        rag_docs = graph.supa.invoke(
            rag_q,
            k=req.rag_k,
            probes=getattr(req, "rag_probes", None) or 12,
        )
    except Exception:
        rag_docs = []

    # 4) Sentez
    prompt = build_synthesis_prompt(req.question, web_items, rag_docs)
    try:
        out = graph.llm.invoke(prompt)
        answer = out.content if hasattr(out, "content") else str(out)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")

    # 5) Kaynaklar (web/scholar görsel yok; RAG görsel linkleri var)
    sources: List[HybridSource] = []

    # web/scholar
    for it in web_items:
        sources.append(
            HybridSource(
                kind="scholar" if it.get("source") == "scholar" else "web",
                title=it.get("title"),
                url=it.get("url"),
                snippet=it.get("snippet"),
                # intentionally no images for web
            )
        )

    # rag (görsel linkleri ile)
    for d in rag_docs:
        md = getattr(d, "metadata", {}) or {}
        img, imgs = _extract_visual_links(md)
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
