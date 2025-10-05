# agentic_rag/ingest/loaders.py
import os
import json
import glob
import re
import hashlib
from urllib.parse import urlparse
from typing import List, Dict, Any
from langchain_core.documents import Document

# filter out base64, obvious sprite paths and svg icons
ICON_HOST_PAT = re.compile(r"(^data:)|(/static/img/)|(\.svg($|\?))", re.I)


def _is_http_url(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _norm_images(images_raw: Any, limit: int = 20) -> List[Dict[str, str]]:
    """
    Accepts list[str] or list[dict]; returns [{'url':..., 'caption':...}]
    Filters icons/base64/svg and non-http(s). Deduplicates. Limits length.
    """
    out: List[Dict[str, str]] = []
    seen = set()
    if not images_raw:
        return out

    for it in images_raw:
        if isinstance(it, str):
            url, cap = it.strip(), ""
        elif isinstance(it, dict):
            url = (it.get("url") or it.get("src") or "").strip()
            cap = (it.get("caption") or it.get("alt") or "").strip()
        else:
            continue

        if not url or ICON_HOST_PAT.search(url) or not _is_http_url(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "caption": cap})
        if len(out) >= limit:
            break
    return out


def _listify(x):
    return x if isinstance(x, list) else [x] if x else []


def _stable_doc_id(payload: Dict[str, Any], fallback: str) -> str:
    """
    Prefer DOI or URL; otherwise hash a few stable fields.
    """
    doi = (payload.get("doi") or "").strip()
    url = (payload.get("url") or "").strip()
    if doi:
        return doi
    if url:
        return url
    h = hashlib.sha256()
    for k in ("title", "publication_date", "source"):
        v = (payload.get(k) or "").strip() if isinstance(
            payload.get(k), str) else str(payload.get(k))
        h.update(v.encode("utf-8"))
    h.update(fallback.encode("utf-8"))
    return h.hexdigest()


def _one_doc_from_ncbi_dict(d: Dict[str, Any], file_basename: str) -> Document | None:
    row, scr = d.get("row", {}) or {}, d.get("scrape", {}) or {}

    title = (row.get("\ufeffTitle") or row.get(
        "Title") or scr.get("title") or "").strip()
    link = (row.get("Link") or scr.get("url") or "").strip()
    abstract = (scr.get("abstract") or "").strip()
    full_text = (scr.get("full_text") or "").strip()

    doi = (scr.get("doi") or "").strip()
    pub_date = (scr.get("publication_date") or "").strip()
    authors = [a for a in _listify(
        scr.get("authors")) if isinstance(a, str) and a.strip()]
    headings = [h for h in _listify(
        scr.get("headings")) if isinstance(h, str) and h.strip()]

    images = _norm_images(scr.get("images"))
    captions_text = "\n".join(
        f"[image] {img['caption']}" for img in images if img["caption"])

    blocks = [
        title,
        f"URL: {link}" if link else "",
        f"DOI: {doi}" if doi else "",
        f"Authors: {', '.join(authors)}" if authors else "",
        f"Published: {pub_date}" if pub_date else "",
        "",
        "Abstract:",
        abstract,
        "",
        "Headings:",
        "\n".join(headings[:30]) if headings else "",
        "",
        "Body:",
        full_text,
        "",
        "Figure captions (from JSON):",
        captions_text,
    ]
    content = "\n".join(b for b in blocks if b is not None)

    if not content.strip():
        return None

    meta = {
        "title": title,
        "url": link,
        "doi": doi or None,
        "publication_date": pub_date or None,
        "authors": authors or None,
        "headings": headings or None,
        "images": [img["url"] for img in images] or None,
        "source": file_basename,
    }
    meta["doc_id"] = _stable_doc_id(
        {**meta, "url": link, "doi": doi, "title": title,
            "publication_date": pub_date, "source": file_basename},
        file_basename,
    )

    return Document(page_content=content, metadata=meta)


def load_ncbi_json_docs(path_or_file: str) -> List[Document]:
    """
    Loads one file or a folder of files and returns a list[Document].
    Supports files whose root is either a dict or a list[dict].
    """
    files = [path_or_file]
    if os.path.isdir(path_or_file):
        files = sorted(glob.glob(os.path.join(path_or_file, "*.json")))

    docs: List[Document] = []
    for p in files:
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)

        items = raw if isinstance(raw, list) else [raw]
        base = os.path.basename(p)

        for idx, d in enumerate(items):
            if not isinstance(d, dict):
                continue
            doc = _one_doc_from_ncbi_dict(d, base)
            if doc:
                docs.append(doc)
    return docs
