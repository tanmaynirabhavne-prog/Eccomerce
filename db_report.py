import sqlite3
conn = sqlite3.connect("ecommerce.db")
conn.row_factory = sqlite3.Row

print("=" * 60)
print("USERS")
print("=" * 60)
for row in conn.execute("SELECT id, username, email FROM users ORDER BY id"):
    print(f"  [{row['id']}] {row['username']} <{row['email']}>")

print()
print("=" * 60)
print("ORDERS (with items)")
print("=" * 60)
orders = conn.execute("""
    SELECT o.id, o.user_id, u.username, o.total, o.status, o.address, o.payment_method
    FROM orders o
    JOIN users u ON u.id = o.user_id
    ORDER BY o.id DESC
""").fetchall()

for o in orders:
    print(f"\nOrder #{o['id']} — {o['username']} — {o['status']} — ${o['total']:.2f} — {o['payment_method']}")
    print(f"  Ship to: {o['address']}")
    items = conn.execute("""
        SELECT oi.quantity, oi.price, p.name
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    """, (o['id'],)).fetchall()
    for item in items:
        print(f"    - {item['name']}  x{item['quantity']}  @ ${item['price']:.2f}")

if not orders:
    print("  (no orders yet)")

print()
print("=" * 60)
print("CURRENT CART CONTENTS")
print("=" * 60)
cart_rows = conn.execute("""
    SELECT c.id, u.username, p.name, c.quantity, p.price
    FROM cart c
    JOIN users u ON u.id = c.user_id
    JOIN products p ON p.id = c.product_id
""").fetchall()

for row in cart_rows:
    print(f"  {row['username']}: {row['name']} x{row['quantity']} @ ${row['price']:.2f}")

if not cart_rows:
    print("  (no items in any cart)")
