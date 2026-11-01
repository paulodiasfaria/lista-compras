"""
Corre isto UMA VEZ na consola Bash da PythonAnywhere para migrar a primeira
compra (Pingo Doce) para a base de dados de produção:

    cd ~/lista-compras
    python3.10 migrate_first_receipt.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "compras.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
INSERT INTO purchases (store_type, store_name, purchase_date, total, total_paid, savings,
                        receipt_photo_path, added_by, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", ("Supermercado", "Pingo Doce - 90 Doce de Carlos Mardel", None, 110.24, 106.59, 3.65,
      None, "Paulo"))

purchase_id = cur.lastrowid

items = [
    ("Mercearia", "B.Cracker PD 200g", "2x€0,69", 0.69, 1.38, None),
    ("Mercearia", "Leite Coco PD 400ml", None, None, 1.39, None),
    ("Mercearia", "Feijão E PD 820/520g", None, None, 1.15, None),
    ("Mercearia", "B. Argolas PD 128g", None, None, 0.99, None),
    ("Mercearia", "Barra Linha Choc PD", None, None, 1.49, None),
    ("Mercearia", "Caps Pr Chave D'Ouro", None, None, 5.99, 0.60),
    ("Mercearia", "Café Mu Int.Bel 200g", None, None, 4.89, 1.80),
    ("Mercearia", "Chá Verde PD 25saq", None, None, 0.99, None),
    ("Mercearia", "Arroz Basmati PD", None, None, 1.89, None),
    ("Mercearia", "Arroz Vaporiz PD", None, None, 1.35, None),
    ("Mercearia", "Café Mu Intenso 250g", None, None, 2.95, None),
    ("Mercearia", "Caps Ar Chave D'Ouro", None, None, 5.99, 0.60),
    ("Mercearia", "Milho Bonduelle 3x70g", None, None, 2.74, None),
    ("Mercearia", "Arroz Ag Urug PD", None, None, 1.39, None),
    ("Mercearia", "Arroz Carolino PD", None, None, 1.15, None),
    ("Mercearia", "B.Cracker PD14x35,7g", None, None, 1.69, None),
    ("Mercearia", "B. Matinais PD 6x50g", "2x€1,99", 1.99, 3.98, None),
    ("Mercearia", "Feijão P PD 420/260g", None, None, 0.84, None),
    ("Take-Away", "Frango Churrasco", "0,874kg x €7,99", 7.99, 6.98, None),
    ("Padaria", "Pão Forma Shape 360g", None, None, 2.99, 0.10),
    ("Frutas e Vegetais", "Cebola Granel", "1,872kg x €1,69", 1.69, 3.16, None),
    ("Frutas e Vegetais", "Brócolos", "0,304kg x €2,99", 2.99, 0.91, None),
    ("Frutas e Vegetais", "Pimento Verde", "0,142kg x €2,89", 2.89, 0.41, None),
    ("Frutas e Vegetais", "Curgete", "0,566kg x €1,89", 1.89, 1.07, 0.40),
    ("Frutas e Vegetais", "Pepino", "0,255kg x €1,99", 1.99, 0.51, None),
    ("Frutas e Vegetais", "Agrião 150g", None, None, 1.49, None),
    ("Frutas e Vegetais", "Pimento Vermelho", "0,310kg x €2,89", 2.89, 0.90, None),
    ("Frutas e Vegetais", "Banana Importada", "0,672kg x €1,19", 1.19, 0.80, None),
    ("Frutas e Vegetais", "Tomate Rosa Seleção", "0,696kg x €2,99", 2.99, 2.08, None),
    ("Frutas e Vegetais", "Espargos Verdes", None, None, 3.19, None),
    ("Frutas e Vegetais", "Cenoura Granel", "0,472kg x €1,09", 1.09, 0.51, None),
    ("Frutas e Vegetais", "Nabos s/Rama", "0,534kg x €2,19", 2.19, 1.17, None),
    ("Frutas e Vegetais", "Maçã Reineta Parda", "1,088kg x €2,39", 2.39, 2.60, None),
    ("Congelados", "Croquete/Bac Salgado 950ml", None, None, 2.89, None),
    ("Congelados", "Pastel Bacalhau 320g", None, None, 4.89, None),
    ("Congelados", "Rissol Leitão 4x85g", None, None, 2.99, None),
    ("Leite", "Bebida Amêndoa s/açúcar 1L", None, None, 1.29, None),
    ("Leite", "Bebida Aveia 0% 1L", None, None, 0.99, 0.05),
    ("Leite", "Bebida Aveia Sab.Leite 1L", None, None, 1.34, 0.05),
    ("Leite", "Bebida Amêndoa/Aveia 1L", None, None, 1.39, 0.05),
    ("Produtos Lácteos", "Iogurte Natural 8x125g", None, None, 1.39, None),
    ("Produtos Lácteos", "Iogurte Grego 4x125g", None, None, 1.68, None),
    ("Produtos Lácteos", "Iogurte Mag. Pedaços Morango 4x125g", "4x€0,36", 0.36, 1.44, None),
    ("Produtos Lácteos", "Iogurte Mag. Pedaços Ananás 4x125g", "4x€0,36", 0.36, 1.44, None),
    ("Queijos", "Queijo Flamengo Fatiado 500g", None, None, 3.99, None),
    ("Queijos", "Queijo Roquefort 100g", None, None, 1.89, None),
    ("Queijos", "Queijo Brie 200g", None, None, 1.65, None),
    ("Pronto a Comer", "Pizza Presunto/Sersuina 390g", None, None, 2.89, None),
    ("Bebidas", "Cerveja Cergal 6x33cl", None, None, 2.79, None),
    ("Bebidas", "Cerveja c/Álcool Sagres", "2x€0,85", 0.85, 1.70, None),
    ("Produtos Pessoais", "Papel Higiénico 6=12", None, None, 2.39, None),
    ("Depósito Volta", "Depósito garrafas", "2x€0,10", 0.10, 0.20, None),
]

for cat, name, qty, unit, total, disc in items:
    cur.execute("""
        INSERT INTO purchase_items (purchase_id, category, product_name, quantity, unit_price, line_total, discount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (purchase_id, cat, name, qty, unit, total, disc))

conn.commit()

cur.execute("SELECT COUNT(*), SUM(line_total) FROM purchase_items WHERE purchase_id=?", (purchase_id,))
count, total_sum = cur.fetchone()
print(f"Compra #{purchase_id} gravada em produção: {count} itens, soma = €{total_sum:.2f}")
conn.close()
