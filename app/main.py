from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware

from .database import engine, SessionLocal
from . import models
from .routers import auth, products, cart, orders, dataset_search


# ---------------- APP ----------------
app = FastAPI(title="E-Commerce API")



# ---------------- SESSION MIDDLEWARE ----------------
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key_12345"
)

# ---------------- CREATE TABLES ----------------
models.Base.metadata.create_all(bind=engine)


def ensure_product_columns():
    with engine.begin() as connection:
        inspector = inspect(connection)
        columns = {column["name"] for column in inspector.get_columns("products")}
        if "category" not in columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR"))
        if "image" not in columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN image VARCHAR"))
        if "external_id" not in columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN external_id VARCHAR"))


def seed_products():
    ensure_product_columns()
    db = SessionLocal()
    try:
        sample_products = [
            models.Product(name="Men Overshirt", price=89.0, stock=10, category="Men", image="https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Men Tailored Jacket", price=120.0, stock=8, category="Men", image="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Men Sneakers", price=95.0, stock=12, category="Men", image="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Men Leather Loafers", price=108.0, stock=6, category="Men", image="https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Men Knit Polo", price=74.0, stock=14, category="Men", image="https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Satin Dress", price=110.0, stock=7, category="Women", image="https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Knit Set", price=78.0, stock=9, category="Women", image="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Heeled Boots", price=132.0, stock=5, category="Women", image="https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Linen Blazer", price=96.0, stock=8, category="Women", image="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Weekend Bag", price=88.0, stock=10, category="Women", image="https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Running Shoes", price=84.0, stock=15, category="Shoes", image="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Leather Loafers", price=102.0, stock=6, category="Shoes", image="https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Minimal Runner", price=116.0, stock=9, category="Shoes", image="https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Signature Hoodie", price=92.0, stock=11, category="Accessories", image="https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Classic Watch", price=210.0, stock=4, category="Accessories", image="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Men Oversized T-Shirt", price=45.0, stock=20, category="Men", image="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Women Ribbed Top", price=52.0, stock=16, category="Women", image="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Classic Denim Jacket", price=98.0, stock=12, category="Men", image="https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=800&q=80"),
            models.Product(name="Canvas High-Top Sneakers", price=82.0, stock=18, category="Shoes", image="https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3?auto=format&fit=crop&w=800&q=80"),
        ]

        for product in sample_products:
            existing = db.query(models.Product).filter(models.Product.name == product.name).first()
            if not existing:
                db.add(product)

        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    seed_products()
    try:
        from app.ml.dataset_search import _get_dataset, get_dataset_item
        _get_dataset()
    except Exception as e:
        print(f"WARNING: dataset search index not loaded: {e}")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- TEMPLATES ----------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------------- ROUTERS ----------------
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(dataset_search.router)

# ---------------- ROOT ----------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# ---------------- FRONTEND PAGES ----------------
@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/products-page")
def products_page(request: Request):
    return templates.TemplateResponse("products.html", {"request": request})

@app.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail_page(product_id: int, request: Request):
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
    finally:
        db.close()
    if not product:
        return templates.TemplateResponse(
            "product_detail.html",
            {"request": request, "product": None},
            status_code=404,
        )
    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product},
    )

@app.get("/dataset-search/{article_id}/open", response_class=HTMLResponse)
def dataset_item_detail_page(article_id: str, request: Request):
    item = get_dataset_item(article_id)
    if not item:
        return templates.TemplateResponse(
            "dataset_item_detail.html",
            {"request": request, "item": None},
            status_code=404,
        )
    return templates.TemplateResponse(
        "dataset_item_detail.html",
        {"request": request, "item": item},
    )
@app.get("/cart-page", response_class=HTMLResponse)
def cart_page(request: Request):
    return templates.TemplateResponse(
        "cart.html",
        {"request": request}
    )

@app.get("/orders-page")
def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/checkout")
def checkout_page(
    request: Request
):

    return templates.TemplateResponse(
        "checkout.html",
        {
            "request":request
        }
    )

@app.get("/women", response_class=HTMLResponse)
def women_page(request: Request):
    return templates.TemplateResponse("women.html", {"request": request})

@app.get("/men", response_class=HTMLResponse)
def men_page(request: Request):
    return templates.TemplateResponse("men.html", {"request": request})

@app.get("/shoes", response_class=HTMLResponse)
def shoes_page(request: Request):
    return templates.TemplateResponse("shoes.html", {"request": request})

