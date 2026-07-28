from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
 
from ..schemas import OrderCreate
from ..dependencies import get_db
from ..crud import create_order, get_orders, get_order_items
 
router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)
 
 
def _serialize_order(db: Session, order):
    items = get_order_items(db, order.id)
    return {
        "id": order.id,
        "user_id": order.user_id,
        "total": order.total,
        "status": order.status,
        "address": order.address,
        "payment_method": order.payment_method,
        "items": [
            {
                "product_id": product.id,
                "name": product.name,
                "quantity": item.quantity,
                "price": item.price,
                "image": getattr(product, "image", None),
            }
            for item, product in items
        ],
    }
 
 
@router.post("/create")
def place_order(
    order: OrderCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
 
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )
 
    new_order = create_order(db, user_id, order)
 
    if new_order is None:
        raise HTTPException(status_code=400, detail="Cart is empty")
 
    return _serialize_order(db, new_order)
 
 
@router.get("/")
def list_orders(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
 
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )
 
    orders = get_orders(db, user_id)
    return [_serialize_order(db, o) for o in orders]
 
 
@router.get("/{order_id}")
def get_order_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
 
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )
 
    orders = get_orders(db, user_id)
    order = next((o for o in orders if o.id == order_id), None)
 
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
 
    return _serialize_order(db, order)
 
