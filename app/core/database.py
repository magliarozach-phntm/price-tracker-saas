import sqlite3

conn = sqlite3.connect("data/prices.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    product TEXT,
    price REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

def save_price(product: str, price: float):
    cursor.execute(
        "INSERT INTO price_history (product, price) VALUES (?, ?)",
        (product, price)
    )
    conn.commit()