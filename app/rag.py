
from sentence_transformers import SentenceTransformer
import faiss
import os
import numpy as np
from glob import glob

_MODEL = None
_INDEX = None
_DOCS = []
_DIM = 384  # default for all-MiniLM-L6-v2


def load_rag(recipes_dir="recipes"):
    global _MODEL, _INDEX, _DOCS, _DIM
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    files = sorted(glob(os.path.join(recipes_dir, "*.txt")))
    docs = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            docs.append(f"# source: {os.path.basename(f)}\n" + fh.read())
    if not docs:
        _DOCS = []
        _INDEX = None
        return
    _DOCS = docs
    embeddings = _MODEL.encode(docs, convert_to_numpy=True, show_progress_bar=False)
    dim = embeddings.shape[1]
    _DIM = dim
    _INDEX = faiss.IndexFlatL2(dim)
    _INDEX.add(np.array(embeddings).astype("float32"))


def retrieve_top_k(query, k=1):
    global _MODEL, _INDEX, _DOCS
    if _INDEX is None or not _DOCS:
        return []
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    q_emb = _MODEL.encode([query], convert_to_numpy=True).astype("float32")
    D, I = _INDEX.search(q_emb, k)
    results = []
    for idx in I[0]:
        if idx < len(_DOCS):
            results.append(_DOCS[idx])
    return results

