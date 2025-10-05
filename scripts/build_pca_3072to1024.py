# scripts/build_pca_3072to1024.py
import os
import glob
import json
import numpy as np
from dotenv import load_dotenv
from joblib import dump
from tqdm import tqdm
from sklearn.decomposition import PCA
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
CORPUS_DIR = os.getenv("JSON_PATH", "data/corpus")
OUT_PATH = os.getenv("PCA_PATH", "models/pca_3072to1024.joblib")
N_COMPONENTS = int(os.getenv("PCA_COMPONENTS", "1024"))

emb = GoogleGenerativeAIEmbeddings(
    model=EMBED_MODEL, google_api_key=GOOGLE_API_KEY)


def iter_texts(max_files=5000):
    files = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.json")))
    for i, p in enumerate(files):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        row, scr = d.get("row", {}), d.get("scrape", {})
        title = row.get("\ufeffTitle") or row.get(
            "Title") or scr.get("title") or ""
        abstract = scr.get("abstract", "") or ""
        full = scr.get("full_text", "") or ""
        text = "\n\n".join(t for t in [title, abstract, full] if t)
        if text.strip():
            yield text
        if i + 1 >= max_files:
            break


samples = list(iter_texts())
X = np.array([emb.embed_query(t)
             for t in tqdm(samples, desc="Embedding sample")], dtype=np.float32)

pca = PCA(n_components=N_COMPONENTS, svd_solver="auto", random_state=42)
pca.fit(X)

explained = pca.explained_variance_ratio_.sum()
print(f"Explained variance: {explained*100:.2f}% with {N_COMPONENTS} dims")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
dump(pca, OUT_PATH)
print("Saved PCA to", OUT_PATH)
