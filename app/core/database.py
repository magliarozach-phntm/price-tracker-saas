import sqlite3

import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "prices.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)

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