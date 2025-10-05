from fastapi import APIRouter, Request, HTTPException
from typing import List, Tuple, Any, Optional
from urllib.parse import urlparse
from server.schemas import (
    AskRequest, AskResponse, SourceItem,
    SearchRequest, SearchResponse, SearchHit
)

router = APIRouter(prefix="/rag", tags=["rag"])

# ---- link extraction helpers ------------------------------------------------

# metadata'da rastlanabilecek anahtarlar
IMG_KEYS = (
    "images", "figures", "thumbnails", "imgs", "pics", "graphics",
    "figure_images", "preview_images",
)
SINGLE_IMG_KEYS = ("image", "thumbnail", "first_image", "cover", "cover_image")
FAVICON_KEYS = ("favicon", "icon", "site_icon")

URL_KEYS = ("src", "url", "href", "image", "link", "data-src", "data-original")


def _ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _pick_url(obj: Any) -> Optional[str]:
    """Extract a single URL from a str OR dict with common url-ish keys."""
    if isinstance(obj, str):
        u = obj.strip()
        return u or None
    if isinstance(obj, dict):
        for k in URL_KEYS:
            v = obj.get(k)
            if isinstance(v, str):
                u = v.strip()
                if u:
                    return u
    return None


def _looks_like_visual(u: str) -> bool:
    """
    'Görsel' benzeri link mi?
    - Gerçek görüntü uzantıları: .jpg/.png/.gif/.webp vb. => kabul
    - Uzantısız ama figure/fig/images/bin uçları => kabul
    - Logo/icon/sprite/svg/static img => red
    """
    if not u:
        return False
    s = u.lower().strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        return False

    # açıkça istemediğimiz ikon/asset kalıpları
    blacklist_tokens = ("logo", "icon", "sprite",
                        "favicon", "/static/img", ".svg")
    if any(tok in s for tok in blacklist_tokens):
        return False

    # gerçek image uzantıları
    img_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
    if any(s.endswith(ext) for ext in img_exts):
        return True

    # figure/fig/images/bin gibi uçlar çoğu dergide figure sayfası/asset'i taşır
    if "/figure" in s or "/fig" in s or "/images" in s or "/bin/" in s:
        return True

    return False


def _ncbi_pmc_fallbacks(page_url: Optional[str]) -> List[str]:
    """
    NCBI/PMC makaleleri için hiç görsel bulunamazsa,
    figure bölümü/assetleri için makul link fallbacks döndür.
    (Ham link; UI bunu tıklanabilir gösterir.)
    """
    if not page_url:
        return []
    try:
        u = page_url.strip().rstrip("/")
        host = urlparse(u).netloc.lower()
        if "ncbi.nlm.nih.gov" in host and "/pmc/articles/" in u:
            # ör: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3630201/
            return [u + "/#figures", u + "/bin/", u + "/pdf"]
    except Exception:
        pass
    return []


def _dedup_keep_order(urls: List[str]) -> List[str]:
    seen = set()
    out = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _extract_favicon(md: dict) -> Optional[str]:
    for k in FAVICON_KEYS:
        v = md.get(k)
        u = _pick_url(v)
        if u:
            return u
    return None


def _extract_visual_links(md: dict) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Metadata'dan görsel benzeri linkleri topla ve normalize et.
    DÖNER: (image, images)
      - image: ilk 'mantıklı' link (UI kartı thumbnail için)
      - images: tüm aday linkler (uzantısız figure sayfası linkleri dahil)
    """
    # 1) Tekil alanlardan yakala
    prim: Optional[str] = None
    pool: List[str] = []

    for k in SINGLE_IMG_KEYS:
        v = md.get(k)
        u = _pick_url(v)
        if u and _looks_like_visual(u):
            prim = prim or u
            pool.append(u)

    # 2) Listeli alanlar
    for k in IMG_KEYS:
        if k in md and md[k]:
            for item in _ensure_list(md[k]):
                u = _pick_url(item)
                # Burada uzantısı olmasa da figure/fig/images/bin linklerini kabul ediyoruz;
                # ikon/sprite/logo/svg/static img'leri eliyoruz.
                if u and _looks_like_visual(u):
                    pool.append(u)

    # 3) Hiçbir şey yoksa: domain-özel fallback (PMC)
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


# ---- source builders --------------------------------------------------------

def _extract_sources(state) -> List[SourceItem]:
    docs = state.get("graded_docs") or state.get("docs") or []
    items: List[SourceItem] = []
    for d in docs:
        md = getattr(d, "metadata", None) or {}
        image, images = _extract_visual_links(md)
        items.append(
            SourceItem(
                title=md.get("title"),
                url=md.get("url") or md.get("source"),
                doc_id=md.get("doc_id"),
                similarity=md.get("similarity"),
                snippet=_excerpt(getattr(d, "page_content", "")),
                type="rag",
                image=image,        # tek link (thumbnail gibi kullan)
                images=images,      # TÜM linkler (figure page/bin/pdf dahil)
                rank=md.get("rank"),
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
        image, images = _extract_visual_links(md)
        hits.append(
            SearchHit(
                title=md.get("title"),
                url=md.get("url") or md.get("source"),
                doc_id=md.get("doc_id"),
                similarity=md.get("similarity"),
                snippet=_excerpt(d.page_content or ""),
                image=image,
                images=images,
                favicon=_extract_favicon(md),
            )
        )
    return SearchResponse(hits=hits)
