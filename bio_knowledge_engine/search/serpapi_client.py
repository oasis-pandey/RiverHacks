import os
import re
import io
import time
import tempfile
import requests
from typing import List, Dict, Any, Optional

from serpapi import GoogleSearch
from bs4 import BeautifulSoup

# PDF -> text (PyMuPDF)
import fitz  # PyMuPDF

# ---- config (SERPAPI_KEY .env'den gelir) ----
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT = 15
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


# ======================
# Google WEB (SerpAPI)
# ======================
def search_web_serpapi(query: str, num: int = 6) -> List[Dict[str, Any]]:
    """SerpAPI Google web sonuçları."""
    if not SERPAPI_KEY:
        return []
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "safe": "active",
    }
    try:
        res = GoogleSearch(params).get_dict()
        items = res.get("organic_results", []) or []
        out = []
        for it in items:
            out.append({
                "title": it.get("title"),
                "link": it.get("link"),
                "snippet": it.get("snippet"),
                "source": it.get("source"),
            })
        return out
    except Exception:
        return []


# =========================
# Google Scholar (SerpAPI)
# =========================
def search_scholar_serpapi(query: str, num: int = 6) -> List[Dict[str, Any]]:
    if not SERPAPI_KEY:
        return []
    params = {
        "engine": "google_scholar",
        "q": query,
        "num": num,
        "api_key": SERPAPI_KEY,
    }
    try:
        res = GoogleSearch(params).get_dict()
        items = res.get("organic_results", []) or []
        out = []
        for it in items:
            title = it.get("title")
            link = it.get("link")
            snippet = it.get("snippet", "")
            pub = it.get("publication_info", {}).get("summary", "")

            pdf_url = None
            for r in it.get("resources", []) or []:
                if r.get("file_format") == "PDF":
                    pdf_url = r.get("link")
                    break

            pdf_text = extract_pdf_text(pdf_url) if pdf_url else None
            out.append({
                "title": title,
                "link": link,
                "snippet": snippet,
                "publication_info": pub,
                "pdf_url": pdf_url,
                "pdf_text": pdf_text,
            })
        return out
    except Exception:
        return []


# ======================
# Web sayfası "skim"
# ======================
BLOCK_TAGS = {"p", "li"}
KEEP_HEADINGS = {"h1", "h2", "h3"}


def fetch_url_text(url: str, max_chars: int = 4000) -> Optional[str]:
    """Basit, hızlı içerik çıkarma: p/li + başlıklar, script/style temizliği."""
    try:
        r = SESSION.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "lxml")

        for s in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
            s.decompose()

        parts: List[str] = []
        # başlıkları ekle
        for h in KEEP_HEADINGS:
            for node in soup.find_all(h):
                t = node.get_text(" ", strip=True)
                if t:
                    parts.append(f"{h.upper()}: {t}")

        # paragraflar/listeler
        for node in soup.find_all(BLOCK_TAGS):
            t = node.get_text(" ", strip=True)
            if t and len(t) > 40:
                parts.append(t)

        text = "\n".join(parts).strip()
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars] if text else None
    except Exception:
        return None


def skim_webpages(web_results: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """İlk N web sonucunun metnini kısaca çıkar."""
    out = []
    for it in web_results[:limit]:
        url = it.get("link")
        if not url:
            continue
        txt = fetch_url_text(url)
        out.append({
            "title": it.get("title"),
            "url": url,
            "text": txt or "",
        })
    return out


# ======================
# PDF -> Text
# ======================
def extract_pdf_text(pdf_url: Optional[str], max_pages: int = 6) -> Optional[str]:
    """PDF'i indir → hızlıca metin çıkar → dosyayı sil. (daha az bellek/tıkanma)"""
    if not pdf_url:
        return None
    try:
        r = SESSION.get(pdf_url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(r.content)
            tmp_path = f.name

        text_parts: List[str] = []
        with fitz.open(tmp_path) as doc:
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                text_parts.append(page.get_text("text"))

        txt = " ".join(text_parts)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:8000] if txt else None
    except Exception:
        return None
    finally:
        try:
            if 'tmp_path' in locals():
                os.remove(tmp_path)
        except Exception:
            pass


# ======================
# Orchestrator
# ======================
def build_external_context(
    query: str,
    use_web: bool = True,
    use_scholar: bool = True,
    scrape_web: bool = True,
    web_num: int = 6,
    scholar_num: int = 6,
) -> Dict[str, Any]:
    """
    Dış kaynakları hazırlar:
    - web: SerpAPI google araması
    - skim: web sonuçlarının ilk N sayfasından hızlı metin
    - scholar: Scholar sonuçları (+ PDF varsa kısa metin)
    """
    result: Dict[str, Any] = {"web": [], "skim": [], "scholar": []}
    if use_web:
        result["web"] = search_web_serpapi(query, num=web_num)
        if scrape_web and result["web"]:
            result["skim"] = skim_webpages(
                result["web"], limit=min(3, web_num))
    if use_scholar:
        result["scholar"] = search_scholar_serpapi(query, num=scholar_num)
    return result

# --- Backward compatibility alias ---


def fetch_scholar_results(query: str, num_results: int = 5):
    """Compat: eski kodun çağırdığı isim. Yeni fonksiyona delege eder."""
    return search_scholar_serpapi(query, num=num_results)
