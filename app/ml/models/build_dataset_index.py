"""
Builds a FAISS vector index over the H&M dataset for semantic search.

Location: app/ml/models/build_dataset_index.py
Reads:    app/ml/dataset/articles_hm.csv (via preprocessing.py)
Writes:   app/ml/artifacts/dataset_tfidf_vectorizer.pkl
          app/ml/artifacts/dataset_svd.pkl
          app/ml/artifacts/dataset_faiss.index
          app/ml/artifacts/dataset_lookup.pkl

HOW IT WORKS
------------
1. Loads and cleans the H&M dataset (105k products).
2. Vectorizes each product's combined text (name, type, colour,
   department, description, etc.) with TF-IDF.
3. Reduces the sparse TF-IDF vectors to dense 128-dimensional vectors
   with Truncated SVD (a form of LSA -- captures the main semantic
   structure of the text in a compact vector).
4. L2-normalizes the vectors, so inner product = cosine similarity.
5. Builds a FAISS IndexFlatIP (exact inner-product search) over these
   vectors -- this is the "vector database" that powers fast semantic
   search at query time.
6. Saves the vectorizer, SVD model, FAISS index, and a lookup table
   (row position -> product info) to disk.

This is a ONE-TIME (or occasional) build step -- re-run it only if the
underlying dataset changes. It does NOT need to be re-run when your
store's own product database changes (that's train_model.py's job).

RUN
---
    python build_dataset_index.py
(from app/ml/models/, or adjust paths if run elsewhere)

REQUIRES
--------
    pip install faiss-cpu
"""

import os
import joblib
import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import sys  # noqa: E402
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from preprocessing import load_and_clean  # noqa: E402

ARTIFACTS_DIR = os.path.join(SCRIPT_DIR, "..", "artifacts")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "dataset_tfidf_vectorizer.pkl")
SVD_PATH = os.path.join(ARTIFACTS_DIR, "dataset_svd.pkl")
FAISS_INDEX_PATH = os.path.join(ARTIFACTS_DIR, "dataset_faiss.index")
LOOKUP_PATH = os.path.join(ARTIFACTS_DIR, "dataset_lookup.pkl")

N_COMPONENTS = 128
MAX_FEATURES = 20000


def build():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print("Loading and cleaning H&M dataset...")
    df = load_and_clean()
    print(f"  {len(df)} products loaded.")

    print("Vectorizing text with TF-IDF...")
    vectorizer = TfidfVectorizer(stop_words="english", max_features=MAX_FEATURES)
    tfidf = vectorizer.fit_transform(df["combined_features"])
    print(f"  TF-IDF matrix shape: {tfidf.shape}")

    print(f"Reducing to {N_COMPONENTS}-dim dense vectors with TruncatedSVD...")
    svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=42)
    dense = svd.fit_transform(tfidf)
    dense = normalize(dense).astype("float32")
    print(f"  Dense vectors shape: {dense.shape}")
    print(f"  Explained variance: {svd.explained_variance_ratio_.sum():.2%}")

    print("Building FAISS index (inner product = cosine similarity, since normalized)...")
    index = faiss.IndexFlatIP(N_COMPONENTS)
    index.add(dense)
    print(f"  FAISS index size: {index.ntotal} vectors")

    lookup = df.drop(columns=["combined_features"]).reset_index(drop=True)

    print("Saving artifacts...")
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(svd, SVD_PATH)
    faiss.write_index(index, FAISS_INDEX_PATH)
    joblib.dump(lookup, LOOKUP_PATH)

    print(f"Done. Artifacts saved to: {os.path.abspath(ARTIFACTS_DIR)}")


if __name__ == "__main__":
    build()