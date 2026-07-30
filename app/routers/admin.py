from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")


def get_conn():
    conn = sqlite3.connect("ecommerce.db")
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@router.post("/admin/login")
def admin_login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Incorrect password"})


@router.get("/admin/logout")
def admin_logout(request: Request):
    request.session.pop("is_admin", None)
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/admin")
def admin_dashboard(request: Request):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/admin/login", status_code=303)

    conn = get_conn()
    users = conn.execute("SELECT id, username, email FROM users ORDER BY id").fetchall()

    orders = conn.execute("""
        SELECT o.id, o.user_id, u.username, o.total, o.status, o.address, o.payment_method
        FROM orders o
        JOIN users u ON u.id = o.user_id
        ORDER BY o.id DESC
    """).fetchall()

    orders_with_items = []
    for o in orders:
        items = conn.execute("""
            SELECT oi.quantity, oi.price, p.name
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (o["id"],)).fetchall()
        orders_with_items.append({"order": o, "line_items": items})

    cart_rows = conn.execute("""
        SELECT c.id, u.username, p.name, c.quantity, p.price
        FROM cart c
        JOIN users u ON u.id = c.user_id
        JOIN products p ON p.id = c.product_id
    """).fetchall()

    conn.close()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "users": users,
        "orders_with_items": orders_with_items,
        "cart_rows": cart_rows,
    })
