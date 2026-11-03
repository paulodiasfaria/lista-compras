CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Outros',
    quantity TEXT,
    unit_price REAL,                 -- preco unitario editavel manualmente
    desired_qty INTEGER NOT NULL DEFAULT 1,  -- nº unidades pretendidas
    notes TEXT,
    added_by TEXT,
    bought INTEGER NOT NULL DEFAULT 0,
    bought_by TEXT,
    bought_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_type TEXT NOT NULL,
    store_name TEXT NOT NULL,
    purchase_date TEXT,              -- YYYY-MM-DD, pode ser NULL se desconhecida
    total REAL NOT NULL,             -- total antes de descontos (soma das linhas)
    total_paid REAL,                 -- total a pagar (depois de descontos), se diferente
    savings REAL,                    -- poupanca total do recibo
    receipt_photo_path TEXT,
    added_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    category TEXT,
    product_name TEXT NOT NULL,
    quantity TEXT,                   -- texto livre, ex: "2x€0,69" ou "0,874kg x €7,99"
    unit_price REAL,
    line_total REAL NOT NULL,
    discount REAL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id)
);

CREATE TABLE IF NOT EXISTS pending_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_path TEXT NOT NULL,
    uploaded_by TEXT,
    uploaded_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | processed
    processed_purchase_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_shopping_list_bought ON shopping_list(bought);
CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_pending_receipts_status ON pending_receipts(status);
