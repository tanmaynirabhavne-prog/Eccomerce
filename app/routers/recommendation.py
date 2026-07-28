"""
FastAPI router for product recommendations.

Location: app/routers/recommendation.py

Exposes:
    GET /recommendations/{article_id}?top_n=10

Wire this up in your main app (e.g. app/main.py) with:
    from app.routers import recommendation
    app.include_router(recommendation.router)

NOTE ON IMPORTS: this assumes your project is run as a package rooted at
`app` (e.g. `uvicorn app.main:app`), matching the __init__.py you already
have at app/__init__.py. If app/ml doesn't have an __init__.py yet, add an
empty one at app/ml/__init__.py so `from app.ml.recommend import ...` works.
"""

from fastapi import APIRouter, HTTPException, Query

from app.ml.recommend import get_similar_products, ArtifactsNotFoundError

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{article_id}")
def recommend_products(
    article_id: str,
    top_n: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
):
    """
    Return products similar to the given article_id, based on shared
    product attributes (type, group, colour, department, description).
    """
    try:
        results = get_similar_products(article_id, top_n=top_n)
    except ArtifactsNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Recommendation model not ready: {e}",
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"article_id '{article_id}' not found in catalog.",
        )

    return {
        "article_id": article_id,
        "count": len(results),
        "recommendations": results,
    }