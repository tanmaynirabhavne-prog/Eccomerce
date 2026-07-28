"""
Inference module for the content-based recommendation engine, trained on
YOUR store's own product database.

Location: app/ml/recommend.py
Reads:    app/ml/artifacts/*.pkl  (produced by models/train_model.py)

Public function:
    get_similar_products(product_id: int, top_n: int = 6) -> list[dict]

Artifacts are loaded once at import time (module-level singletons) so
repeated calls -- e.g. from a FastAPI endpoint -- are fast and don't
re-read the pickle files from disk on every request.

USAGE
-----
    from app.ml.recommend import get_similar_products
    results = get_similar_products(5, top_n=4)
"""

import os
import joblib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(SCRIPT_DIR, "artifacts")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "tfidf_vectorizer.pkl")
NN_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "nn_model.pkl")
LOOKUP_PATH = os.path.join(ARTIFACTS_DIR, "product_lookup.pkl")

_nn_model = None
_lookup = None  # list of dicts: {"id", "name", "price", "category", "image"}
_tfidf_matrix = None
_product_id_to_row = None


class ArtifactsNotFoundError(Exception):
    pass


def _load_artifacts():
    """Lazily load model artifacts once, cache them at module level."""
    global _nn_model, _lookup, _tfidf_matrix, _product_id_to_row

    if _nn_model is not None:
        return  # already loaded

    missing = [
        p for p in (VECTORIZER_PATH, NN_MODEL_PATH, LOOKUP_PATH)
        if not os.path.isfile(p)
    ]
    if missing:
        missing_list = "\n  - ".join(missing)
        raise ArtifactsNotFoundError(
            f"Missing model artifact(s):\n  - {missing_list}\n\n"
            f"Run `python -m app.ml.models.train_model` from your project "
            f"root first to generate them."
        )

    _nn_model = joblib.load(NN_MODEL_PATH)
    saved = joblib.load(LOOKUP_PATH)
    _lookup = saved["lookup"]
    _tfidf_matrix = saved["tfidf_matrix"]
    _product_id_to_row = {p["id"]: idx for idx, p in enumerate(_lookup)}


def get_similar_products(product_id: int, top_n: int = 6) -> list:
    """
    Return up to `top_n` products most similar to `product_id`,
    ordered by similarity (most similar first). Excludes the queried
    product itself.

    Returns a list of dicts, e.g.:
        [{"id": 3, "name": "...", "price": 89.99, "category": "Sneakers",
          "image": "...", "similarity": 0.83}, ...]

    Raises:
        ArtifactsNotFoundError: if the model hasn't been trained yet.
        KeyError: if product_id isn't in the trained catalog (e.g. it was
                  added after the last training run -- retrain to include it).
    """
    _load_artifacts()

    if product_id not in _product_id_to_row:
        raise KeyError(
            f"product_id {product_id} not found in the trained model. "
            f"If this product was added recently, retrain the model."
        )

    row_idx = _product_id_to_row[product_id]
    query_vector = _tfidf_matrix[row_idx]

    n_neighbors = min(top_n + 1, _nn_model.n_neighbors)
    distances, indices = _nn_model.kneighbors(
        query_vector, n_neighbors=n_neighbors
    )

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == row_idx:
            continue  # skip the queried product itself
        p = _lookup[idx]
        results.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "category": p["category"],
            "image": p["image"],
            "similarity": round(float(1 - dist), 4),
        })
        if len(results) >= top_n:
            break

    return results