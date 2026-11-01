"""
Lista de Compras - app partilhada para Paulo e Rita.

Arquitetura:
- Flask + SQLite (ficheiro local, mesmo padrao do eventos-app).
- Lista ativa de compras (shopping_list) partilhada entre os dois.
- Historico de compras (purchases + purchase_items), uma entrada por viagem
  ao supermercado/farmacia/etc, com recibo fotografado opcional.
- Upload de foto de recibo fica "pendente" (pending_receipts) - o
  processamento (ler a foto, extrair produtos/precos) e feito pelo agente
  Hermes manualmente quando o utilizador pede ("processa recibos pendentes"),
  nao automaticamente - sem custo de API de visao extra.
- Rotas /api/* protegidas por X-API-Key, usadas só pelo agente (consultar
  pendentes, submeter resultado do processamento). Rotas normais (lista,
  historico, adicionar item, marcar comprado) sao de uso direto, sem chave.
"""
import os
import re
import sqlite3
from datetime import date, datetime

from flask import Flask, g, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

DB_PATH = os.environ.get("COMPRAS_DB_PATH", os.path.join(os.path.dirname(__file__), "compras.db"))
API_KEY = os.environ.get("COMPRAS_API_KEY", "changeme-dev-key")
UPLOAD_DIR = os.environ.get("COMPRAS_UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

CATEGORIAS = ["Supermercado", "Farmácia", "Talho", "Peixaria", "Outros"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with open(os.path.join(os.path.dirname(__file__), "schema.sql"), encoding="utf-8") as f:
            db.executescript(f.read())
        db.commit()


def require_api_key():
    key = request.headers.get("X-API-Key")
    if key != API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    return None


def guess_category(product_name):
    name = product_name.lower()
    farmacia_kw = ["paracetamol", "ibuprofeno", "pasta de dentes", "xarope", "vitamina", "band-aid", "curativo"]
    talho_kw = ["carne", "frango", "bife", "costeleta", "picada", "chouriço", "salsicha"]
    peixaria_kw = ["peixe", "salmão", "bacalhau", "camarão", "atum fresco"]
    if any(k in name for k in farmacia_kw):
        return "Farmácia"
    if any(k in name for k in talho_kw):
        return "Talho"
    if any(k in name for k in peixaria_kw):
        return "Peixaria"
    return "Supermercado"


def get_avg_price(db, product_name):
    """Media do preco das ultimas 2 compras deste produto (match exato,
    case-insensitive, sobre purchase_items). None se nunca foi comprado."""
    rows = db.execute(
        """SELECT pi.line_total FROM purchase_items pi
           JOIN purchases p ON p.id = pi.purchase_id
           WHERE LOWER(pi.product_name) = LOWER(?)
           ORDER BY p.id DESC, pi.id DESC
           LIMIT 2""",
        (product_name,),
    ).fetchall()
    if not rows:
        return None
    return sum(r["line_total"] for r in rows) / len(rows)


GRAMS_PATTERN = re.compile(r"(?:(\d+)\s*[Xx]\s*)?(\d+(?:[.,]\d+)?)\s*[Gg]\b")


def extract_total_grams(product_name):
    """Extrai o peso total em gramas do nome do produto, ex:
    '200G' -> 200, '6X50G' -> 300, '14X35,7G' -> 499.8. None se nao achar."""
    match = GRAMS_PATTERN.search(product_name)
    if not match:
        return None
    multiplier = int(match.group(1)) if match.group(1) else 1
    weight = float(match.group(2).replace(",", "."))
    return multiplier * weight


def price_display(avg_price, product_name):
    """Devolve (valor, unidade) para mostrar: preco/kg se o produto tiver
    peso em gramas no nome, senao preco/un normal."""
    if avg_price is None:
        return None, None
    grams = extract_total_grams(product_name)
    if grams:
        return avg_price / (grams / 1000), "kg"
    return avg_price, "un"


def get_frequent_products(db, limit=8, exclude_names=None):
    """Produtos mais comprados no historico (por numero de vezes),
    excluindo os que ja estao na lista ativa."""
    exclude_names = {n.lower() for n in (exclude_names or [])}
    rows = db.execute(
        """SELECT product_name, category, COUNT(*) AS n
           FROM purchase_items
           GROUP BY LOWER(product_name)
           ORDER BY n DESC, product_name ASC"""
    ).fetchall()
    result = []
    for r in rows:
        if r["product_name"].lower() in exclude_names:
            continue
        result.append({"product_name": r["product_name"], "category": r["category"]})
        if len(result) >= limit:
            break
    return result


# ---------------------------------------------------------------------------
# Paginas
# ---------------------------------------------------------------------------

@app.route("/")
def lista():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM shopping_list ORDER BY bought ASC, created_at ASC"
    ).fetchall()

    by_category = {}
    avg_prices = {}
    for r in rows:
        by_category.setdefault(r["category"], []).append(r)
        avg = get_avg_price(db, r["product_name"])
        value, unit = price_display(avg, r["product_name"])
        avg_prices[r["id"]] = {"value": value, "unit": unit}

    active_names = [r["product_name"] for r in rows]
    frequent = get_frequent_products(db, limit=8, exclude_names=active_names)

    pending_count = db.execute(
        "SELECT COUNT(*) AS c FROM pending_receipts WHERE status='pending'"
    ).fetchone()["c"]

    # gastos deste mes vs mes passado
    today = date.today()
    cur_month = today.strftime("%Y-%m")
    if today.month == 1:
        prev_month = f"{today.year - 1}-12"
    else:
        prev_month = f"{today.year}-{today.month - 1:02d}"

    cur_total = db.execute(
        "SELECT COALESCE(SUM(total_paid), SUM(total), 0) AS t FROM purchases WHERE purchase_date LIKE ?",
        (f"{cur_month}%",),
    ).fetchone()["t"] or 0
    prev_total = db.execute(
        "SELECT COALESCE(SUM(total_paid), SUM(total), 0) AS t FROM purchases WHERE purchase_date LIKE ?",
        (f"{prev_month}%",),
    ).fetchone()["t"] or 0
    delta_pct = None
    if prev_total:
        delta_pct = round((cur_total - prev_total) / prev_total * 100)

    return render_template(
        "lista.html",
        active_page="lista",
        by_category=by_category,
        avg_prices=avg_prices,
        frequent=frequent,
        categorias=sorted(by_category.keys()),
        pending_count=pending_count,
        cur_total=cur_total,
        delta_pct=delta_pct,
    )


@app.route("/items/add", methods=["POST"])
def add_item():
    db = get_db()
    product_name = request.form.get("product_name", "").strip()
    if not product_name:
        return redirect(url_for("lista"))
    category = request.form.get("category") or guess_category(product_name)
    quantity = request.form.get("quantity", "").strip() or None
    added_by = request.form.get("added_by", "").strip() or None
    db.execute(
        "INSERT INTO shopping_list (product_name, category, quantity, added_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (product_name, category, quantity, added_by, datetime.now().isoformat(timespec="seconds")),
    )
    db.commit()
    return redirect(url_for("lista"))


@app.route("/items/<int:item_id>/toggle", methods=["POST"])
def toggle_item(item_id):
    db = get_db()
    row = db.execute("SELECT bought FROM shopping_list WHERE id=?", (item_id,)).fetchone()
    if row is None:
        return redirect(url_for("lista"))
    new_bought = 0 if row["bought"] else 1
    bought_by = request.form.get("bought_by", "").strip() or None
    bought_at = datetime.now().isoformat(timespec="seconds") if new_bought else None
    db.execute(
        "UPDATE shopping_list SET bought=?, bought_by=?, bought_at=? WHERE id=?",
        (new_bought, bought_by if new_bought else None, bought_at, item_id),
    )
    db.commit()
    return redirect(url_for("lista"))


@app.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("lista"))


@app.route("/historico")
def historico():
    db = get_db()
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    store_type = request.args.get("store_type", "")
    store_name = request.args.get("store_name", "")

    query = "SELECT * FROM purchases WHERE 1=1"
    params = []
    if date_from:
        query += " AND (purchase_date IS NULL OR purchase_date >= ?)"
        params.append(date_from)
    if date_to:
        query += " AND (purchase_date IS NULL OR purchase_date <= ?)"
        params.append(date_to)
    if store_type:
        query += " AND store_type = ?"
        params.append(store_type)
    if store_name:
        query += " AND store_name = ?"
        params.append(store_name)
    query += " ORDER BY purchase_date DESC, id DESC"

    purchases = db.execute(query, params).fetchall()
    purchases_with_items = []
    for p in purchases:
        items = db.execute(
            "SELECT * FROM purchase_items WHERE purchase_id=? ORDER BY id", (p["id"],)
        ).fetchall()
        purchases_with_items.append({"purchase": p, "line_items": items})

    store_types = [r["store_type"] for r in db.execute(
        "SELECT DISTINCT store_type FROM purchases ORDER BY store_type"
    ).fetchall()]
    store_names = [r["store_name"] for r in db.execute(
        "SELECT DISTINCT store_name FROM purchases ORDER BY store_name"
    ).fetchall()]

    return render_template(
        "historico.html",
        active_page="historico",
        purchases_with_items=purchases_with_items,
        store_types=store_types,
        store_names=store_names,
        filters={"date_from": date_from, "date_to": date_to, "store_type": store_type, "store_name": store_name},
    )


@app.route("/receipts/upload", methods=["POST"])
def upload_receipt():
    file = request.files.get("photo")
    uploaded_by = request.form.get("uploaded_by", "").strip() or None
    if file and file.filename:
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file.save(os.path.join(UPLOAD_DIR, filename))
        db = get_db()
        db.execute(
            "INSERT INTO pending_receipts (photo_path, uploaded_by, uploaded_at, status) VALUES (?, ?, ?, 'pending')",
            (filename, uploaded_by, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
    return redirect(url_for("historico"))


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve fotos de recibos - pública (sem X-API-Key) para poder ser aberta
    diretamente num <img> e também lida pelo agente Hermes via URL https
    (o agente não tem acesso ao disco do servidor, só via HTTP)."""
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------------------------------------------------------------------
# API (usada pelo agente Hermes para processar recibos pendentes)
# ---------------------------------------------------------------------------

@app.route("/api/receipts/pending", methods=["GET"])
def api_pending_receipts():
    unauthorized = require_api_key()
    if unauthorized:
        return unauthorized
    db = get_db()
    rows = db.execute(
        "SELECT * FROM pending_receipts WHERE status='pending' ORDER BY uploaded_at"
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["photo_url"] = url_for("serve_upload", filename=r["photo_path"], _external=True)
        result.append(d)
    return jsonify(result)


@app.route("/api/receipts/<int:receipt_id>/process", methods=["POST"])
def api_process_receipt(receipt_id):
    """
    Body esperado (JSON):
    {
      "store_type": "Supermercado", "store_name": "Pingo Doce - X",
      "purchase_date": "2026-10-31" (opcional),
      "total": 110.24, "total_paid": 106.59, "savings": 3.65,
      "items": [
        {"category": "Mercearia", "product_name": "...", "quantity": "2x€0,69",
         "unit_price": 0.69, "line_total": 1.38, "discount": null},
        ...
      ]
    }
    Marca itens correspondentes da shopping_list ativa como comprados
    (match por nome, case-insensitive, substring simples).
    """
    unauthorized = require_api_key()
    if unauthorized:
        return unauthorized
    db = get_db()
    receipt = db.execute("SELECT * FROM pending_receipts WHERE id=?", (receipt_id,)).fetchone()
    if receipt is None:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(force=True)
    db.execute(
        """INSERT INTO purchases (store_type, store_name, purchase_date, total, total_paid, savings,
                                   receipt_photo_path, added_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("store_type", "Supermercado"),
            data.get("store_name", "Desconhecida"),
            data.get("purchase_date"),
            data.get("total", 0),
            data.get("total_paid"),
            data.get("savings"),
            receipt["photo_path"],
            receipt["uploaded_by"],
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    purchase_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    active_items = db.execute("SELECT id, product_name FROM shopping_list WHERE bought=0").fetchall()

    checked_off = []
    for item in data.get("items", []):
        db.execute(
            """INSERT INTO purchase_items (purchase_id, category, product_name, quantity, unit_price,
                                            line_total, discount)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                purchase_id,
                item.get("category"),
                item["product_name"],
                item.get("quantity"),
                item.get("unit_price"),
                item["line_total"],
                item.get("discount"),
            ),
        )
        # tenta cruzar com a lista ativa (match simples por substring, case-insensitive)
        item_name_lower = item["product_name"].lower()
        for active in active_items:
            if active["product_name"].lower() in item_name_lower or item_name_lower in active["product_name"].lower():
                db.execute(
                    "UPDATE shopping_list SET bought=1, bought_by='auto (recibo)', bought_at=? WHERE id=?",
                    (datetime.now().isoformat(timespec="seconds"), active["id"]),
                )
                checked_off.append(active["product_name"])

    db.execute(
        "UPDATE pending_receipts SET status='processed', processed_purchase_id=? WHERE id=?",
        (purchase_id, receipt_id),
    )
    db.commit()
    return jsonify({"purchase_id": purchase_id, "checked_off_items": checked_off})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True, port=5001)
else:
    # Quando importado via WSGI (produção), garante sempre que o esquema
    # existe - CREATE TABLE IF NOT EXISTS e idempotente, seguro chamar sempre.
    init_db()
