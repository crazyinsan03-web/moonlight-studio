from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

# -------- DATABASE --------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_no TEXT,
        item TEXT,
        qty REAL,
        price INTEGER,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route('/')
def home():
    return render_template("home.html")

# -------- WAITER --------
@app.route('/waiter')
def waiter():
    table_no = request.args.get('table')

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status!='paid'"
    ).fetchall()
    conn.close()

    tables = {}

    for row in rows:
        t = row["table_no"]

        if t not in tables:
            tables[t] = {
                "orders": [],
                "status": "pending"
            }

        tables[t]["orders"].append(row)

        if row["status"] == "preparing":
            tables[t]["status"] = "preparing"
        elif row["status"] == "ready":
            if tables[t]["status"] != "preparing":
                tables[t]["status"] = "ready"

    orders = []
    if table_no and table_no in tables:
        orders = tables[table_no]["orders"]

    return render_template("waiter.html",
                           tables=tables,
                           orders=orders,
                           table_no=table_no)

# -------- ADD ITEM (UPDATED 🔥) --------
@app.route('/add_item/<table_no>', methods=['POST'])
def add_item(table_no):
    item = request.form['item']
    qty = float(request.form['qty'])
    type_ = request.form['type']

    item_name = f"{item} ({type_})"

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM orders WHERE table_no=? AND item=? AND status!='paid'",
        (table_no, item_name)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE orders SET qty = qty + ? WHERE id=?",
            (qty, existing['id'])
        )
    else:
        conn.execute(
            "INSERT INTO orders (table_no, item, qty, price, status) VALUES (?, ?, ?, ?, ?)",
            (table_no, item_name, qty, 0, 'pending')
        )

    # reset status when new item added
    conn.execute(
        "UPDATE orders SET status='pending' WHERE table_no=? AND status!='paid'",
        (table_no,)
    )

    conn.commit()
    conn.close()

    return redirect(f'/waiter?table={table_no}')

# -------- DELETE --------
@app.route('/delete/<int:id>/<table_no>')
def delete(id, table_no):
    conn = get_db()
    conn.execute("DELETE FROM orders WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(f'/waiter?table={table_no}')

# -------- CHEF --------
@app.route('/chef')
def chef():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status!='paid'"
    ).fetchall()
    conn.close()

    tables = {}

    for row in rows:
        t = row["table_no"]
        if t not in tables:
            tables[t] = []
        tables[t].append(row)

    return render_template("chef.html", tables=tables)

# -------- UPDATE STATUS --------
@app.route('/update_table/<table_no>/<status>')
def update_table(table_no, status):
    conn = get_db()
    conn.execute(
        "UPDATE orders SET status=? WHERE table_no=? AND status!='paid'",
        (status, table_no)
    )
    conn.commit()
    conn.close()
    return redirect('/chef')

# -------- RECEPTION --------
@app.route('/reception')
def reception():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status='ready'"
    ).fetchall()
    conn.close()

    tables = {}

    for row in rows:
        t = row["table_no"]
        if t not in tables:
            tables[t] = []
        tables[t].append(row)

    return render_template("reception.html", tables=tables)

# -------- BILL --------
@app.route('/bill/<table_no>')
def bill(table_no):
    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders WHERE table_no=? AND status='ready'",
        (table_no,)
    ).fetchall()

    conn.close()

    return render_template("bill.html", orders=orders, table_no=table_no)

# -------- CALCULATE --------
@app.route('/calculate/<table_no>', methods=['POST'])
def calculate(table_no):
    items = request.form.getlist('item')
    prices = request.form.getlist('price')

    total = sum(int(p) for p in prices)
    gst = round(total * 0.18, 2)
    final = total + gst

    return render_template("bill.html",
                           orders=zip(items, prices),
                           table_no=table_no,
                           total=total,
                           gst=gst,
                           final=final)

# -------- PAYMENT DONE --------
@app.route('/payment_done/<table_no>')
def payment_done(table_no):
    conn = get_db()
    conn.execute("DELETE FROM orders WHERE table_no=?", (table_no,))
    conn.commit()
    conn.close()
    return redirect('/reception')

# -------- INVOICE PDF --------
@app.route('/invoice/<table_no>')
def invoice(table_no):
    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders WHERE table_no=? AND status='ready'",
        (table_no,)
    ).fetchall()

    conn.close()

    file_path = f"invoice_{table_no}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("<b>RMS Restaurant</b>", styles['Title']))
    elements.append(Paragraph("Rajsamand, Rajasthan", styles['Normal']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Table {table_no}", styles['Heading2']))
    elements.append(Paragraph(datetime.now().strftime('%d-%m-%Y %H:%M'), styles['Normal']))
    elements.append(Spacer(1, 10))

    data = [["Item", "Qty", "Price", "Total"]]

    total = 0

    for o in orders:
        item_total = o['qty'] * o['price']
        data.append([o['item'], o['qty'], f"₹{o['price']}", f"₹{item_total}"])
        total += item_total

    gst = round(total * 0.18, 2)
    final = total + gst

    data.append(["", "", "Subtotal", f"₹{total}"])
    data.append(["", "", "GST", f"₹{gst}"])
    data.append(["", "", "Total", f"₹{final}"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you!", styles['Normal']))

    doc.build(elements)

    return send_file(file_path, as_attachment=True)

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
