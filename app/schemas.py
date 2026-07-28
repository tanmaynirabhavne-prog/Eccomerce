from pydantic import BaseModel, EmailStr, Field
from typing import Optional



# ================= USER =================

class UserCreate(BaseModel):

    username: str

    email: EmailStr

    password: str = Field(
        ...,
        min_length=4,
        max_length=72
    )



class UserLogin(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=4,
        max_length=72
    )




# ================= PRODUCT =================

class ProductCreate(BaseModel):

    name: str

    price: float

    stock: int

    category: Optional[str] = "General"

    image: Optional[str] = None




# ================= CART =================

class CartItem(BaseModel):

    product_id: int

    quantity: int





# ================= ORDER =================

class OrderCreate(BaseModel):

    address: str

    payment_method: str = "Cash on Delivery"