# scripts/build_randproj_3072to1024.py
import os
from dotenv import load_dotenv
from joblib import dump
import numpy as np

load_dotenv()

OUT_PATH = os.getenv("RP_PATH", "models/rp_3072to1024.joblib")
IN_DIM = 3072
OUT_DIM = 1024
SEED = int(os.getenv("RP_SEED", "42"))

rng = np.random.default_rng(SEED)
# Gaussian random projection matrix (JL lemma); scale 1/sqrt(OUT_DIM)
W = rng.normal(loc=0.0, scale=1.0/np.sqrt(OUT_DIM),
               size=(OUT_DIM, IN_DIM)).astype(np.float32)

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
dump({"W": W, "in_dim": IN_DIM, "out_dim": OUT_DIM, "seed": SEED}, OUT_PATH)
print("Saved RP matrix to", OUT_PATH)
