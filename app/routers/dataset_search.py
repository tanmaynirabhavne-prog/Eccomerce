"""
FastAPI router for searching the H&M dataset and importing results into
your store when a user adds one to their cart.

Location: app/routers/dataset_search.py

Exposes:
    GET  /dataset-search?q=hoodie&limit=20
         Semantic search over the 105k-product H&M dataset (FAISS-backed).
         Results are informational -- NOT yet in your store's database.

    POST /dataset-search/{article_id}/add-to-cart
         Imports the H&M item into your store's products table (if not
         already imported) and adds it to the logged-in user's cart.
         Requires login, same as your existing /cart/add endpoint.

WHY IMPORT-ON-ADD: the H&M dataset has no price/stock data (it's a
metadata-only catalog), so items can't be "real" store products until
someone actually wants to buy one. At that point we assign a stable,
deterministic price (based on the article_id, so repeated imports of
the same item always get the same price) and create a normal Product
row, tagged with `external_id` so re-adding the same item later reuses
the existing product instead of creating a duplicate.
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_db
from ..crud import add_to_cart
from ..ml.dataset_search import search_dataset, get_dataset_item, get_catalog_image, DatasetIndexNotFoundError

router = APIRouter(prefix="/dataset-search", tags=["Dataset Search"])

PRICE_LOW = 19.99
PRICE_HIGH = 199.99
DEFAULT_STOCK = 50
CATALOG_IMAGES = [
    "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=900&q=85",
]


class AddToCartFromDataset(BaseModel):
    quantity: int = 1


def _deterministic_price(article_id: str) -> float:
    """Stable pseudo-price derived from the article_id (H&M data has no
    price field), so the same item always gets the same price."""
    digest = hashlib.md5(article_id.encode()).hexdigest()
    frac = int(digest[:8], 16) / 0xFFFFFFFF
    return round(PRICE_LOW + frac * (PRICE_HIGH - PRICE_LOW), 2)


def _catalog_image(article_id: str) -> str:
    return CATALOG_IMAGES[int(hashlib.md5(article_id.encode()).hexdigest()[:8], 16) % len(CATALOG_IMAGES)]


def _get_or_import_product(article_id: str, db: Session):
    product = db.query(models.Product).filter(models.Product.external_id == article_id).first()
    if product:
        return product

    item = get_dataset_item(article_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"article_id '{article_id}' not found in dataset.")

    product = models.Product(
        name=item["name"] or "Unnamed Product",
        price=_deterministic_price(article_id),
        stock=DEFAULT_STOCK,
        category=item.get("type") or item.get("department") or "General",
        image=get_catalog_image(article_id),
        external_id=article_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("")
def search(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        results = search_dataset(q, limit=limit)
    except DatasetIndexNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.post("/{article_id}/add-to-cart")
def add_dataset_item_to_cart(
    article_id: str,
    body: AddToCartFromDataset,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Please login first")

    try:
        product = _get_or_import_product(article_id, db)
    except DatasetIndexNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    cart = add_to_cart(db, user_id, product.id, body.quantity)

    return {
        "cart_id": cart.id,
        "product_id": product.id,
        "name": product.name,
        "price": product.price,
        "quantity": cart.quantity,
        "imported": True,
    }


@router.get("/{article_id}/open")
def open_dataset_product(article_id: str, db: Session = Depends(get_db)):
    """Open a dataset result as a normal, purchasable store product."""
    try:
        product = _get_or_import_product(article_id, db)
    except DatasetIndexNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return RedirectResponse(url=f"/product/{product.id}", status_code=303)
