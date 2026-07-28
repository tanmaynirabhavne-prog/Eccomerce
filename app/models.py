from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base


# ---------------- USER ----------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)



class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    category = Column(String, default="General")
    image = Column(String, nullable=True)
    external_id = Column(String, nullable=True)



# ---------------- CART ----------------

class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, default=1)



# ---------------- ORDER ----------------

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float)
    status = Column(String, default="Pending")
    address = Column(String)
    payment_method = Column(String, default="Cash on Delivery")


# ---------------- ORDER ITEMS ----------------

class OrderItem(Base):

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)


    order_id = Column(
        Integer,
        ForeignKey("orders.id")
    )


    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )


    quantity = Column(Integer)


    price = Column(Float)