"""
Trains the content-based similarity model on YOUR store's actual product
catalog (the `products` table in your database) -- not the H&M dataset.

Location: app/ml/models/train_model.py
Reads:    your products table, via SQLAlchemy (app.database / app.models)
Writes:   app/ml/artifacts/tfidf_vectorizer.pkl
          app/ml/artifacts/nn_model.pkl
          app/ml/artifacts/product_lookup.pkl

HOW IT WORKS
------------
1. Queries all products from your DB (same models.Product used by crud.py).
2. Builds a text feature per product: category (repeated x3 to weight it
   heavily) + product name. This means "same category" dominates
   similarity, with name providing finer-grained distinction within a
   category. This suits your schema, which has no long description field.
3. Vectorizes with TF-IDF, fits a NearestNeighbors (cosine) index.
4. Saves the vectorizer, index, and a lookup table (DB id -> product info)
   so recommend.py can map a product id to its neighbors.

RUN
---
Run from your project root (so the `app` package resolves correctly):
    python -m app.ml.models.train_model

Re-run this any time products are added/removed/edited, to keep
recommendations in sync with your catalog.
"""

import os
import sys
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Make sure the project root (parent of "app") is importable, whether this
# is run as `python -m app.ml.models.train_model` or directly.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import SessionLocal  # noqa: E402
from app import models  # noqa: E402

ARTIFACTS_DIR = os.path.join(SCRIPT_DIR, "..", "artifacts")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "tfidf_vectorizer.pkl")
NN_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "nn_model.pkl")
LOOKUP_PATH = os.path.join(ARTIFACTS_DIR, "product_lookup.pkl")

# How many category repeats to weight category over name in similarity.
CATEGORY_WEIGHT = 3


def fetch_products():
    """Pull all products from the DB, same way crud.get_products() does."""
    db = SessionLocal()
    try:
        products = db.query(models.Product).all()
        # Materialize into plain dicts now, while the session is open,
        # so we don't hold the DB session open longer than needed.
        return [
            {
                "id": p.id,
                "name": p.name or "",
                "price": p.price,
                "category": p.category or "General",
                "image": p.image,
            }
            for p in products
        ]
    finally:
        db.close()


def build_text_feature(product: dict) -> str:
    category = (product["category"] or "General").strip()
    name = (product["name"] or "").strip()
    weighted_category = " ".join([category] * CATEGORY_WEIGHT)
    return f"{weighted_category} {name}".lower()


def train():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print("Fetching products from the database...")
    products = fetch_products()
    print(f"  {len(products)} products loaded.")

    if len(products) < 2:
        print(
            "Not enough products to train a similarity model "
            "(need at least 2). Add more products first."
        )
        return

    texts = [build_text_feature(p) for p in products]

    print("Vectorizing product text with TF-IDF...")
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"  TF-IDF matrix shape: {tfidf_matrix.shape}")

    print("Fitting NearestNeighbors index (cosine similarity)...")
    # +1 because a product's own nearest neighbor is always itself
    n_neighbors = min(11, len(products))
    nn_model = NearestNeighbors(
        n_neighbors=n_neighbors,
        metric="cosine",
        algorithm="brute",
    )
    nn_model.fit(tfidf_matrix)

    lookup = products  # list of dicts, index-aligned with tfidf_matrix rows

    print("Saving artifacts...")
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(nn_model, NN_MODEL_PATH)
    joblib.dump(
        {"lookup": lookup, "tfidf_matrix": tfidf_matrix},
        LOOKUP_PATH,
    )

    print(f"Done. Artifacts saved to: {os.path.abspath(ARTIFACTS_DIR)}")


if __name__ == "__main__":
    train()