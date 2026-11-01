"""
Corre isto UMA VEZ (local ou na consola Bash da PythonAnywhere) para preencher
a Lista de Compras ativa com todos os produtos da primeira compra (Pingo
Doce), para nao teres de os escrever manualmente um a um.

    cd ~/lista-compras
    python3.10 seed_list_from_first_purchase.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "compras.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

items = cur.execute(
    "SELECT category, product_name, quantity FROM purchase_items WHERE purchase_id=1 ORDER BY id"
).fetchall()

now = datetime.now().isoformat(timespec="seconds")
added = 0
for item in items:
    exists = cur.execute(
        "SELECT 1 FROM shopping_list WHERE LOWER(product_name)=LOWER(?)", (item["product_name"],)
    ).fetchone()
    if exists:
        continue
    cur.execute(
        "INSERT INTO shopping_list (product_name, category, quantity, added_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (item["product_name"], item["category"], item["quantity"], "Paulo", now),
    )
    added += 1

conn.commit()
print(f"{added} produtos adicionados a lista de compras ativa (de {len(items)} na 1a compra).")
conn.close()
