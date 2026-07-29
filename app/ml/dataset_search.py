"""
Semantic search over the H&M dataset (105k+ products), powered by FAISS.

Location: app/ml/dataset_search.py
Reads:    app/ml/artifacts/dataset_*.pkl and dataset_faiss.index
          (produced by models/build_dataset_index.py)

This is SEPARATE from the store's product recommendation engine
(app/ml/recommend.py, which works on YOUR actual database products).
This module searches the full H&M dataset for informational/browsing
purposes. Results are not in your store's database until a user
explicitly adds one to cart (see routers/dataset_search.py), at which
point it gets imported as a real product.

IMAGE ASSIGNMENT
-----------------
The H&M CSV has no image URLs, so images are assigned deterministically:
- Gender-appropriate pool is chosen from index_name/department_name
  (menswear items get men's photos, womenswear items get women's photos).
- Within a single search_dataset() call, images are de-duplicated so no
  two items in the same result list share a photo.
- get_dataset_item() (single-item lookup, used for the detail page and
  for cart import) uses the same gender pool and the same base hash, so
  it normally matches what was shown in the grid.

Public function:
    search_dataset(query: str, limit: int = 20) -> list[dict]
    get_dataset_item(article_id: str) -> dict | None
    get_catalog_image(article_id: str, index_name=None, department_name=None) -> str
"""

import os
import hashlib
import joblib
import faiss
import requests
from sklearn.preprocessing import normalize

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(SCRIPT_DIR, "artifacts")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "dataset_tfidf_vectorizer.pkl")
SVD_PATH = os.path.join(ARTIFACTS_DIR, "dataset_svd.pkl")
FAISS_INDEX_PATH = os.path.join(ARTIFACTS_DIR, "dataset_faiss.index")
LOOKUP_PATH = os.path.join(ARTIFACTS_DIR, "dataset_lookup.pkl")

_RELEASE_BASE = "https://github.com/tanmaynirabhavne-prog/Eccomerce/releases/download/v1.0-ml-artifacts"
_DOWNLOAD_URLS = {
    VECTORIZER_PATH: f"{_RELEASE_BASE}/dataset_tfidf_vectorizer.pkl",
    SVD_PATH: f"{_RELEASE_BASE}/dataset_svd.pkl",
    FAISS_INDEX_PATH: f"{_RELEASE_BASE}/dataset_faiss.index",
    LOOKUP_PATH: f"{_RELEASE_BASE}/dataset_lookup.pkl",
}

def _download_missing_artifacts():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    for path, url in _DOWNLOAD_URLS.items():
        if os.path.isfile(path):
            continue
        print(f"Downloading missing artifact: {os.path.basename(path)} ...")
        try:
            resp = requests.get(url, stream=True, timeout=120)
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {os.path.basename(path)} ({os.path.getsize(path)} bytes)")
        except Exception as e:
            print(f"Failed to download {os.path.basename(path)}: {e}")

_vectorizer = None
_svd = None
_faiss_index = None
_lookup = None  # DataFrame, index-aligned with the FAISS index


class DatasetIndexNotFoundError(Exception):
    pass


def _load_artifacts():
    global _vectorizer, _svd, _faiss_index, _lookup

    if _faiss_index is not None:
        return

    _download_missing_artifacts()
    missing = [
        p for p in (VECTORIZER_PATH, SVD_PATH, FAISS_INDEX_PATH, LOOKUP_PATH)
        if not os.path.isfile(p)
    ]
    if missing:
        missing_list = "\n  - ".join(missing)
        raise DatasetIndexNotFoundError(
            f"Missing dataset search index file(s):\n  - {missing_list}\n\n"
            f"Run `python build_dataset_index.py` from app/ml/models/ "
            f"first to generate them."
        )

    _vectorizer = joblib.load(VECTORIZER_PATH)
    _svd = joblib.load(SVD_PATH)
    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    _lookup = joblib.load(LOOKUP_PATH)


def _get_dataset():
    """Preload the search index. Call this once at server startup."""
    _load_artifacts()
    return _lookup


# ---------------- IMAGE ASSIGNMENT ----------------

MEN_IMAGE_POOL = [
    'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80',
]

WOMEN_IMAGE_POOL = [
    'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1495121605193-b116b5b9cba6?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=600&q=80',
]


def _get_gender_pool(index_name, department_name):
    text = f"{index_name or ''} {department_name or ''}".lower()
    if any(k in text for k in ("women", "ladies", "girl")):
        return WOMEN_IMAGE_POOL
    if any(k in text for k in ("men", "boy")) and "women" not in text:
        return MEN_IMAGE_POOL
    return MEN_IMAGE_POOL + WOMEN_IMAGE_POOL  # unisex fallback


def _base_index(article_id: str, pool_len: int) -> int:
    digest = hashlib.md5(str(article_id).encode()).hexdigest()
    return int(digest[:8], 16) % pool_len


def get_catalog_image(article_id: str, index_name: str = None, department_name: str = None) -> str:
    """
    Deterministic, gender-appropriate image for a single dataset item.
    Used for single-item lookups (detail page, cart import) where there's
    no sibling list to de-duplicate against.
    """
    pool = _get_gender_pool(index_name, department_name)
    idx = _base_index(article_id, len(pool))
    return pool[idx]


def _assign_images_deduped(rows: list) -> list:
    """
    Assign images to a LIST of rows (each a dict with article_id,
    index_name, department_name), guaranteeing no two rows in this same
    list get the same image. Uses linear probing from the deterministic
    base index.
    """
    used_by_pool = {}
    images = []
    for row in rows:
        pool = _get_gender_pool(row.get("index_name"), row.get("department_name"))
        pool_key = id(pool)
        used = used_by_pool.setdefault(pool_key, set())
        idx = _base_index(row["article_id"], len(pool))
        tries = 0
        while idx in used and tries < len(pool):
            idx = (idx + 1) % len(pool)
            tries += 1
        used.add(idx)
        images.append(pool[idx])
    return images


# ---------------- SEARCH ----------------

def search_dataset(query: str, limit: int = 20) -> list:
    """
    Semantic search: embeds the query the same way the dataset was
    embedded (TF-IDF -> SVD -> normalize), then finds the closest
    vectors in the FAISS index by cosine similarity. Images assigned
    are gender-appropriate and guaranteed unique within this result list.
    """
    query = (query or "").strip()
    if not query:
        return []

    _load_artifacts()

    q_tfidf = _vectorizer.transform([query.lower()])
    q_dense = _svd.transform(q_tfidf)
    q_dense = normalize(q_dense).astype("float32")

    scores, indices = _faiss_index.search(q_dense, limit)

    rows = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        row = _lookup.iloc[idx]
        rows.append({
            "article_id": row.get("article_id"),
            "name": row.get("prod_name"),
            "type": row.get("product_type_name"),
            "colour": row.get("colour_group_name"),
            "department": row.get("department_name"),
            "department_name": row.get("department_name"),
            "index_name": row.get("index_name"),
            "description": (row.get("detail_desc") or "")[:200],
            "similarity": round(float(score), 4),
        })

    images = _assign_images_deduped(rows)
    for row, image in zip(rows, images):
        row["image"] = image
        row.pop("department_name", None)
        row.pop("index_name", None)

    return rows


def get_dataset_item(article_id: str) -> dict:
    """
    Look up a single dataset item by article_id (used for the item detail
    page, and when a user adds a search result to their cart so we can
    import it into the store DB). Returns None if not found.
    """
    _load_artifacts()
    article_id = str(article_id).strip()
    matches = _lookup[_lookup["article_id"] == article_id]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return {
        "article_id": row.get("article_id"),
        "name": row.get("prod_name"),
        "type": row.get("product_type_name"),
        "colour": row.get("colour_group_name"),
        "department": row.get("department_name"),
        "description": (row.get("detail_desc") or "")[:500],
        "image": get_catalog_image(
            row.get("article_id"),
            row.get("index_name"),
            row.get("department_name"),
        ),
    }
