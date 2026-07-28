from sqlalchemy.orm import Session
from . import models
 
 
 
# ================= REGISTER =================
 
def create_user(db: Session, user):
 
    db_user = models.User(
        username=user.username,
        email=user.email,
        password=user.password
    )
 
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
 
    return db_user
 
 
 
# ================= LOGIN =================
 
def authenticate_user(db: Session, email: str, password: str):
 
    user = db.query(models.User).filter(
        models.User.email == email
    ).first()
 
 
    if not user:
        return None
 
 
    if user.password != password:
        return None
 
 
    return user
 
 
 
 
# ================= PRODUCTS =================
 
def create_product(db: Session, product):
 
    db_product = models.Product(
        **product.dict()
    )
 
 
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
 
    return db_product
 
 
 
def get_products(db: Session):
 
    return db.query(
        models.Product
    ).all()
 
 
 
 
 
# ================= CART =================
 
 
def add_to_cart(
    db: Session,
    user_id: int,
    product_id: int,
    qty: int
):
 
    cart = db.query(models.Cart).filter(
        models.Cart.user_id == user_id,
        models.Cart.product_id == product_id
    ).first()
 
 
 
    if cart:
 
        cart.quantity += qty
 
 
    else:
 
        cart = models.Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=qty
        )
 
        db.add(cart)
 
 
 
    db.commit()
    db.refresh(cart)
 
 
    return cart
 
 
 
 
 
def get_cart(
    db: Session,
    user_id: int
):
 
    return (
        db.query(
            models.Cart,
            models.Product
        )
        .join(
            models.Product,
            models.Cart.product_id == models.Product.id
        )
        .filter(
            models.Cart.user_id == user_id
        )
        .all()
    )
 
 
 
 
 
def remove_from_cart(
    db: Session,
    cart_id: int
):
 
    cart = db.query(
        models.Cart
    ).filter(
        models.Cart.id == cart_id
    ).first()
 
 
 
    if cart:
 
        db.delete(cart)
        db.commit()
 
 
 
    return {
        "message": "Item removed from cart"
    }
 
 
 
 
 
def clear_cart(
    db: Session,
    user_id: int
):
 
    db.query(
        models.Cart
    ).filter(
        models.Cart.user_id == user_id
    ).delete()
 
 
    db.commit()
 
 
    return {
        "message": "Cart cleared"
    }
 
 
 
 
 
# ================= ORDERS =================
 
 
def create_order(
    db: Session,
    user_id: int,
    order
):
 
 
    # Get cart items
 
    cart_items = (
        db.query(
            models.Cart,
            models.Product
        )
        .join(
            models.Product,
            models.Cart.product_id == models.Product.id
        )
        .filter(
            models.Cart.user_id == user_id
        )
        .all()
    )
 
 
 
    if not cart_items:
 
        return None
 
 
 
 
    total = 0
 
 
 
    # Calculate total
 
    for cart, product in cart_items:
 
        total += (
            product.price *
            cart.quantity
        )
 
 
 
 
 
    # Create Order
 
 
    db_order = models.Order(
 
        user_id=user_id,
 
        total=total,
 
        status="Pending",
 
        address=order.address,
 
        payment_method=order.payment_method
 
    )
 
 
 
    db.add(db_order)
 
    db.commit()
 
    db.refresh(db_order)
 
 
 
 
 
 
    # Create Order Items
 
 
    for cart, product in cart_items:
 
 
        order_item = models.OrderItem(
 
            order_id=db_order.id,
 
            product_id=product.id,
 
            quantity=cart.quantity,
 
            price=product.price
 
        )
 
 
        db.add(order_item)
 
 
 
 
    db.commit()
 
    # empty the cart now that everything is copied into the order
    clear_cart(db, user_id)
 
    return db_order
 
 
def get_orders(
    db: Session,
    user_id: int
):
 
    return (
        db.query(
            models.Order
        )
        .filter(
            models.Order.user_id == user_id
        )
        .order_by(
            models.Order.id.desc()
        )
        .all()
    )
 
 
def get_order_items(
    db: Session,
    order_id: int
):
 
    return (
        db.query(
            models.OrderItem,
            models.Product
        )
        .join(
            models.Product,
            models.OrderItem.product_id == models.Product.id
        )
        .filter(
            models.OrderItem.order_id == order_id
        )
        .all()
    )
 
