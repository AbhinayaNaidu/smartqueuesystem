from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import math

app = Flask(__name__)
DB_NAME = "queue.db"
SERVICE_TIME = 5  # minutes per person

# ---------------- DB Helpers ----------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_place(place):
    conn = get_db()
    row = conn.execute("SELECT * FROM queues WHERE place=?", (place,)).fetchone()
    if not row:
        conn.execute("INSERT INTO queues VALUES (?,?,?)", (place, 0, datetime.now().isoformat()))
        conn.commit()
    conn.close()

def get_current_queue(place):
    ensure_place(place)
    conn = get_db()
    row = conn.execute("SELECT * FROM queues WHERE place=?", (place,)).fetchone()
    if not row:
        conn.close()
        return 0, 0
    last_update = row["last_update"]
    if not last_update:
        last_update = datetime.now().isoformat()
        conn.execute("UPDATE queues SET last_update=? WHERE place=?", (last_update, place))
        conn.commit()
    last_time = datetime.fromisoformat(last_update)
    now = datetime.now()
    elapsed = (now - last_time).total_seconds() / 60
    served = math.floor(elapsed / SERVICE_TIME)
    new_count = max(row["count"] - served, 0)
    if served > 0:
        conn.execute("UPDATE queues SET count=?, last_update=? WHERE place=?", (new_count, now.isoformat(), place))
        conn.commit()
    conn.close()
    wait_time = new_count * SERVICE_TIME
    return new_count, wait_time

# ---------------- User ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/join", methods=["POST"])
def join():
    place = request.form["place"]
    ensure_place(place)
    count, _ = get_current_queue(place)
    count += 1
    now = datetime.now().isoformat()
    conn = get_db()
    conn.execute("UPDATE queues SET count=?, last_update=? WHERE place=?", (count, now, place))
    conn.commit()
    conn.close()
    wait = count * SERVICE_TIME
    status = "Low" if count <= 2 else "Medium" if count <= 5 else "Heavy"
    return render_template("index.html", place=place, count=count, wait=wait, status=status, time=datetime.now().strftime("%H:%M:%S"))

@app.route("/update_queue", methods=["POST"])
def update_queue():
    place = request.form["place"]
    count, wait = get_current_queue(place)
    status = "Low" if count <= 2 else "Medium" if count <= 5 else "Heavy"
    return jsonify({"count": count, "wait": wait, "status": status, "time": datetime.now().strftime("%H:%M:%S")})

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/dashboard_data")
def dashboard_data():
    conn = get_db()
    rows = conn.execute("SELECT * FROM queues").fetchall()
    conn.close()
    data = []
    for r in rows:
        count, wait = get_current_queue(r["place"])
        status = "Low" if count <= 2 else "Medium" if count <= 5 else "Heavy"
        data.append({"place": r["place"], "count": count, "wait_sec": wait*60, "status": status})
    return jsonify(data)

# ---------------- Admin ----------------
@app.route("/admin")
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM queues").fetchall()
    conn.close()
    return render_template("admin.html", queues=rows)

@app.route("/admin_update", methods=["POST"])
def admin_update():
    place = request.form["place"]
    action = request.form["action"]
    count, _ = get_current_queue(place)
    now = datetime.now().isoformat()
    if action == "add": count += 1
    elif action == "serve": count = max(count-1,0)
    elif action == "reset": count = 0
    conn = get_db()
    conn.execute("UPDATE queues SET count=?, last_update=? WHERE place=?", (count, now, place))
    conn.commit()
    conn.close()
    return "", 204

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

