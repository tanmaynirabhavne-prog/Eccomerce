from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from ..schemas import CartItem
from ..dependencies import get_db
from ..crud import add_to_cart, get_cart, remove_from_cart

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post("/add")
def add_item(
    item: CartItem,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    cart = add_to_cart(
        db,
        user_id,
        item.product_id,
        item.quantity
    )
    return {
        "cart_id": cart.id,
        "user_id": cart.user_id,
        "product_id": cart.product_id,
        "quantity": cart.quantity,
    }


@router.get("/")
def get_my_cart(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    cart_items = get_cart(db, user_id)

    result = []

    for cart_item, product in cart_items:
        result.append({
            "cart_id": cart_item.id,
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": cart_item.quantity,
            "image": getattr(product, "image", None)
        })

    return result


@router.delete("/remove/{cart_id}")
def remove_cart_item(
    cart_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    return remove_from_cart(db, cart_id)
