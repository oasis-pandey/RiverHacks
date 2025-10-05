from __future__ import annotations
import os
import json
import glob
import hashlib
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from .config import PERSIST_DIR, COLLECTION, JSON_PATH, CHUNK_SIZE, CHUNK_OVERLAP


def _sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def load_json_docs(path: str) -> List[Document]:
    files = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.json")))
    else:
        files = [path]

    docs: List[Document] = []
    for p in files:
        with open(p, "rb") as f:
            raw = f.read()
        d = json.loads(raw.decode("utf-8"))
        row = d.get("row", {})
        scr = d.get("scrape", {})

        title = row.get("\ufeffTitle") or row.get(
            "Title", "") or scr.get("title", "")
        link = row.get("Link", "") or scr.get("url", "")

        blocks = [title, link, scr.get("title", ""), scr.get(
            "abstract", ""), scr.get("full_text", "")]
        page_content = "\n\n".join([b for b in blocks if b])
        if not page_content.strip():
            continue

        docs.append(Document(
            page_content=page_content,
            metadata={
                "url": scr.get("url") or link or None,
                "doi": scr.get("doi"),
                "source": os.path.basename(p),
                "title": title,
            }
        ))
    return docs


def ensure_index(embeddings) -> None:
    os.makedirs(PERSIST_DIR, exist_ok=True)
    fp_file = os.path.join(PERSIST_DIR, ".fingerprint")

    if os.path.isdir(JSON_PATH):
        fps = []
        for p in sorted(glob.glob(os.path.join(JSON_PATH, "*.json"))):
            with open(p, "rb") as f:
                fps.append(_sha256_bytes(f.read()))
        new_fp = _sha256_bytes("".join(fps).encode("utf-8"))
    else:
        with open(JSON_PATH, "rb") as f:
            new_fp = _sha256_bytes(f.read())

    old_fp = None
    if os.path.exists(fp_file):
        with open(fp_file, "r", encoding="utf-8") as f:
            old_fp = f.read().strip()

    needs_build = (not os.path.exists(os.path.join(
        PERSIST_DIR, "chroma.sqlite3"))) or (new_fp != old_fp)

    if needs_build:
        docs = load_json_docs(JSON_PATH)
        if not docs:
            raise FileNotFoundError("No valid JSON documents found to index.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.split_documents(docs)

        vs = Chroma.from_documents(
            documents=chunks,
            collection_name=COLLECTION,
            embedding=embeddings,
            persist_directory=PERSIST_DIR,
        )

        with open(fp_file, "w", encoding="utf-8") as f:
            f.write(new_fp)
