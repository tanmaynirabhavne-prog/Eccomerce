from fastapi import APIRouter, Depends, Query, HTTPException
from .. import models
from ..ml.recommend import get_similar_products, ArtifactsNotFoundError
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..dependencies import get_db

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/")
def add_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    created = crud.create_product(db, product)
    return {
        "id": created.id,
        "name": created.name,
        "price": created.price,
        "stock": created.stock,
    }


@router.get("/")
def list_products(
    db: Session = Depends(get_db),
    category: str | None = Query(None, description="Optional category to filter"),
    search: str | None = Query(None, description="Optional product search term")
):
    products = crud.get_products(db)

    if category:
        # Exact match (case-insensitive), not substring — substring matching
        # was letting "men" match "women" since "women" contains "men".
        target = category.strip().lower()
        products = [
            p for p in products
            if (getattr(p, "category", "") or "").strip().lower() == target
        ]

    if search:
        q = search.lower().strip()
        products = [
            p for p in products
            if q in (p.name or "").lower() or q in (getattr(p, "category", "") or "").lower()
        ]

    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "category": getattr(product, "category", None),
            "image": getattr(product, "image", None),
        }
        for product in products
    ]

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "category": product.category,
        "image": product.image,
    }


@router.get("/{product_id}/similar")
def get_similar(product_id: int, top_n: int = Query(default=6, ge=1, le=20)):
    try:
        results = get_similar_products(product_id, top_n=top_n)
    except ArtifactsNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Recommendation model not ready: {e}",
        )
    except KeyError:
        return {"product_id": product_id, "count": 0, "recommendations": []}

    return {
        "product_id": product_id,
        "count": len(results),
        "recommendations": results,
    }