from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, List

from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS

import mysql.connector
from mysql.connector import pooling

from werkzeug.security import check_password_hash


# ----------------------------
# Paths / Frontend serving
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# If frontend is served from same Flask app, CORS isn't necessary,
# but it doesn't hurt during development if you run frontend separately.
CORS(app, supports_credentials=True)


# ----------------------------
# Database (MySQL) connection pool
# ----------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "MY_MYSQL_PASSWORD",
    "database": "logistic_company",
    "autocommit": False,
}

POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

pool = None

def get_pool():
    """Lazy initialization of database connection pool."""
    global pool
    if pool is None:
        try:
            pool = pooling.MySQLConnectionPool(
                pool_name="logistics_pool",
                pool_size=POOL_SIZE,
                **DB_CONFIG,
            )
        except Exception as e:
            print(f"Warning: Database connection failed: {e}")
            print("Frontend will still be served, but API endpoints will fail.")
    return pool


def db_query(
    sql: str,
    params: Tuple[Any, ...] | List[Any] | None = None,
    *,
    fetchone: bool = False,
) -> Any:
    """Run SELECT queries and return rows (dicts)."""
    pool_obj = get_pool()
    if pool_obj is None:
        return None if fetchone else []
    conn = pool_obj.get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetchone:
            return cur.fetchone()
        return cur.fetchall()
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


def db_execute(
    sql: str,
    params: Tuple[Any, ...] | List[Any] | None = None,
) -> Dict[str, Any]:
    """Run INSERT/UPDATE/DELETE queries and commit."""
    pool_obj = get_pool()
    if pool_obj is None:
        return {"error": "Database not available", "affected": 0, "lastrowid": 0}
    conn = pool_obj.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return {"affected": cur.rowcount, "lastrowid": cur.lastrowid}
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


# ----------------------------
# Helpers
# ----------------------------
def api_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def require_login():
    """Very simple auth guard (session-based)."""
    if "user_id" not in session:
        return api_error("Not authenticated", 401)
    return None


def is_password_valid(stored: str, provided: str) -> bool:
    """
    Supports either:
    - hashed password (werkzeug format like 'pbkdf2:sha256:...')
    - plain text (not recommended, but useful for student projects)
    """
    if stored is None:
        return False
    stored = str(stored)

    # Heuristic: werkzeug hashes contain ':' separators and start with an algorithm name.
    if ":" in stored and stored.split(":", 1)[0] in {"pbkdf2", "scrypt", "argon2"}:
        return check_password_hash(stored, provided)

    # fallback: plain text compare
    return stored == provided


def parse_date(date_str: str) -> Optional[str]:
    """
    Accepts 'YYYY-MM-DD' or ISO-like 'YYYY-MM-DDTHH:MM:SS'.
    Returns MySQL friendly 'YYYY-MM-DD HH:MM:SS' or None.
    """
    if not date_str:
        return None
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str)
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


# ----------------------------
# Auth endpoints (session-based)
# ----------------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return api_error("username and password are required", 400)

    user = db_query(
        """
        SELECT u.id, u.username, u.password, r.name AS role
        FROM users u
        JOIN roles r ON r.id = u.role_id
        WHERE u.username = %s
        """,
        (username,),
        fetchone=True,
    )

    if not user or not is_password_valid(user["password"], password):
        return api_error("Invalid credentials", 401)

    # Store minimal identity in session
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify(
        {
            "message": "ok",
            "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
        }
    )


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "ok"})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    return jsonify(
        {
            "authenticated": True,
            "user": {
                "id": session.get("user_id"),
                "username": session.get("username"),
                "role": session.get("role"),
            },
        }
    )


# ----------------------------
# Health check
# ----------------------------
@app.route("/api/health", methods=["GET"])
def health():
    row = db_query("SELECT 1 AS ok", fetchone=True)
    return jsonify(row)


# ----------------------------
# Offices CRUD
# ----------------------------
@app.route("/api/offices", methods=["GET"])
def offices_list():
    rows = db_query("SELECT id, name, address FROM offices ORDER BY id DESC")
    return jsonify(rows)


@app.route("/api/offices/<int:office_id>", methods=["GET"])
def offices_get(office_id: int):
    row = db_query(
        "SELECT id, name, address FROM offices WHERE id=%s",
        (office_id,),
        fetchone=True,
    )
    if not row:
        return api_error("Office not found", 404)
    return jsonify(row)


@app.route("/api/offices", methods=["POST"])
def offices_create():
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    address = (data.get("address") or "").strip()
    if not name or not address:
        return api_error("name and address are required")

    res = db_execute(
        "INSERT INTO offices (name, address) VALUES (%s, %s)",
        (name, address),
    )
    return jsonify(res), 201


@app.route("/api/offices/<int:office_id>", methods=["PUT"])
def offices_update(office_id: int):
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    address = (data.get("address") or "").strip()
    if not name or not address:
        return api_error("name and address are required")

    res = db_execute(
        "UPDATE offices SET name=%s, address=%s WHERE id=%s",
        (name, address, office_id),
    )
    if res["affected"] == 0:
        return api_error("Office not found", 404)
    return jsonify(res)


@app.route("/api/offices/<int:office_id>", methods=["DELETE"])
def offices_delete(office_id: int):
    guard = require_login()
    if guard:
        return guard

    res = db_execute("DELETE FROM offices WHERE id=%s", (office_id,))
    if res["affected"] == 0:
        return api_error("Office not found", 404)
    return jsonify(res)


# ----------------------------
# Clients CRUD
# ----------------------------
@app.route("/api/clients", methods=["GET"])
def clients_list():
    rows = db_query(
        """
        SELECT c.id, c.user_id, u.username, c.name, c.phone, c.email
        FROM clients c
        JOIN users u ON u.id = c.user_id
        ORDER BY c.id DESC
        """
    )
    return jsonify(rows)


@app.route("/api/clients/<int:client_id>", methods=["GET"])
def clients_get(client_id: int):
    row = db_query(
        """
        SELECT c.id, c.user_id, u.username, c.name, c.phone, c.email
        FROM clients c
        JOIN users u ON u.id = c.user_id
        WHERE c.id=%s
        """,
        (client_id,),
        fetchone=True,
    )
    if not row:
        return api_error("Client not found", 404)
    return jsonify(row)


@app.route("/api/clients", methods=["POST"])
def clients_create():
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None

    if not user_id or not name:
        return api_error("user_id and name are required")

    # Ensure user exists
    u = db_query("SELECT id FROM users WHERE id=%s", (user_id,), fetchone=True)
    if not u:
        return api_error("User not found", 404)

    res = db_execute(
        "INSERT INTO clients (user_id, name, phone, email) VALUES (%s, %s, %s, %s)",
        (user_id, name, phone, email),
    )
    return jsonify(res), 201


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def clients_update(client_id: int):
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None

    if not name:
        return api_error("name is required")

    res = db_execute(
        "UPDATE clients SET name=%s, phone=%s, email=%s WHERE id=%s",
        (name, phone, email, client_id),
    )
    if res["affected"] == 0:
        return api_error("Client not found", 404)
    return jsonify(res)


@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
def clients_delete(client_id: int):
    guard = require_login()
    if guard:
        return guard

    res = db_execute("DELETE FROM clients WHERE id=%s", (client_id,))
    if res["affected"] == 0:
        return api_error("Client not found", 404)
    return jsonify(res)


# ----------------------------
# Employees CRUD
# ----------------------------
@app.route("/api/employees", methods=["GET"])
def employees_list():
    rows = db_query(
        """
        SELECT e.id, e.user_id, u.username, e.name, e.position, e.office_id, o.name AS office_name
        FROM employees e
        JOIN users u ON u.id = e.user_id
        LEFT JOIN offices o ON o.id = e.office_id
        ORDER BY e.id DESC
        """
    )
    return jsonify(rows)


@app.route("/api/employees/<int:employee_id>", methods=["GET"])
def employees_get(employee_id: int):
    row = db_query(
        """
        SELECT e.id, e.user_id, u.username, e.name, e.position, e.office_id, o.name AS office_name
        FROM employees e
        JOIN users u ON u.id = e.user_id
        LEFT JOIN offices o ON o.id = e.office_id
        WHERE e.id=%s
        """,
        (employee_id,),
        fetchone=True,
    )
    if not row:
        return api_error("Employee not found", 404)
    return jsonify(row)


@app.route("/api/employees", methods=["POST"])
def employees_create():
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    name = (data.get("name") or "").strip()
    position = (data.get("position") or "").strip() or None
    office_id = data.get("office_id")

    if not user_id or not name:
        return api_error("user_id and name are required")

    # Ensure user exists
    u = db_query("SELECT id FROM users WHERE id=%s", (user_id,), fetchone=True)
    if not u:
        return api_error("User not found", 404)

    if office_id is not None:
        o = db_query("SELECT id FROM offices WHERE id=%s", (office_id,), fetchone=True)
        if not o:
            return api_error("Office not found", 404)

    res = db_execute(
        "INSERT INTO employees (user_id, name, position, office_id) VALUES (%s, %s, %s, %s)",
        (user_id, name, position, office_id),
    )
    return jsonify(res), 201


@app.route("/api/employees/<int:employee_id>", methods=["PUT"])
def employees_update(employee_id: int):
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    position = (data.get("position") or "").strip() or None
    office_id = data.get("office_id")

    if not name:
        return api_error("name is required")

    if office_id is not None:
        o = db_query("SELECT id FROM offices WHERE id=%s", (office_id,), fetchone=True)
        if not o:
            return api_error("Office not found", 404)

    res = db_execute(
        "UPDATE employees SET name=%s, position=%s, office_id=%s WHERE id=%s",
        (name, position, office_id, employee_id),
    )
    if res["affected"] == 0:
        return api_error("Employee not found", 404)
    return jsonify(res)


@app.route("/api/employees/<int:employee_id>", methods=["DELETE"])
def employees_delete(employee_id: int):
    guard = require_login()
    if guard:
        return guard

    res = db_execute("DELETE FROM employees WHERE id=%s", (employee_id,))
    if res["affected"] == 0:
        return api_error("Employee not found", 404)
    return jsonify(res)


# ----------------------------
# Shipments CRUD + status
# ----------------------------
@app.route("/api/shipments", methods=["GET"])
def shipments_list():
    """
    Optional query params:
      - status=SENT|RECEIVED
      - client_id=...
      - employee_id=...
    """
    status = (request.args.get("status") or "").strip().upper() or None
    client_id = request.args.get("client_id")
    employee_id = request.args.get("employee_id")

    where = []
    params: List[Any] = []

    if status in {"SENT", "RECEIVED"}:
        where.append("s.status = %s")
        params.append(status)

    if client_id:
        where.append("(s.sender_client_id=%s OR s.receiver_client_id=%s)")
        params.extend([client_id, client_id])

    if employee_id:
        where.append("s.registered_by_employee_id=%s")
        params.append(employee_id)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db_query(
        f"""
        SELECT
          s.id,
          s.sender_client_id, sc.name AS sender_name,
          s.receiver_client_id, rc.name AS receiver_name,
          s.weight, s.delivery_type, s.delivery_address,
          s.price, s.status,
          s.registered_by_employee_id, e.name AS registered_by_name,
          s.created_at, s.received_at
        FROM shipments s
        JOIN clients sc ON sc.id = s.sender_client_id
        JOIN clients rc ON rc.id = s.receiver_client_id
        JOIN employees e ON e.id = s.registered_by_employee_id
        {where_sql}
        ORDER BY s.id DESC
        """,
        tuple(params),
    )
    return jsonify(rows)


@app.route("/api/shipments/<int:shipment_id>", methods=["GET"])
def shipments_get(shipment_id: int):
    row = db_query(
        """
        SELECT
          s.id,
          s.sender_client_id, sc.name AS sender_name,
          s.receiver_client_id, rc.name AS receiver_name,
          s.weight, s.delivery_type, s.delivery_address,
          s.price, s.status,
          s.registered_by_employee_id, e.name AS registered_by_name,
          s.created_at, s.received_at
        FROM shipments s
        JOIN clients sc ON sc.id = s.sender_client_id
        JOIN clients rc ON rc.id = s.receiver_client_id
        JOIN employees e ON e.id = s.registered_by_employee_id
        WHERE s.id=%s
        """,
        (shipment_id,),
        fetchone=True,
    )
    if not row:
        return api_error("Shipment not found", 404)
    return jsonify(row)


@app.route("/api/shipments", methods=["POST"])
def shipments_create():
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    sender_client_id = data.get("sender_client_id")
    receiver_client_id = data.get("receiver_client_id")
    weight = data.get("weight")
    delivery_type = (data.get("delivery_type") or "").strip().upper()
    delivery_address = (data.get("delivery_address") or "").strip() or None
    price = data.get("price")
    registered_by_employee_id = data.get("registered_by_employee_id")

    if not all([sender_client_id, receiver_client_id, weight, delivery_type, price, registered_by_employee_id]):
        return api_error("Missing required fields")

    if delivery_type not in {"OFFICE", "ADDRESS"}:
        return api_error("delivery_type must be OFFICE or ADDRESS")

    # Validate foreign keys exist
    if not db_query("SELECT id FROM clients WHERE id=%s", (sender_client_id,), fetchone=True):
        return api_error("Sender client not found", 404)
    if not db_query("SELECT id FROM clients WHERE id=%s", (receiver_client_id,), fetchone=True):
        return api_error("Receiver client not found", 404)
    if not db_query("SELECT id FROM employees WHERE id=%s", (registered_by_employee_id,), fetchone=True):
        return api_error("Employee not found", 404)

    res = db_execute(
        """
        INSERT INTO shipments
        (sender_client_id, receiver_client_id, weight, delivery_type, delivery_address, price, status, registered_by_employee_id)
        VALUES (%s, %s, %s, %s, %s, %s, 'SENT', %s)
        """,
        (sender_client_id, receiver_client_id, weight, delivery_type, delivery_address, price, registered_by_employee_id),
    )
    return jsonify(res), 201


@app.route("/api/shipments/<int:shipment_id>", methods=["PUT"])
def shipments_update(shipment_id: int):
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    weight = data.get("weight")
    delivery_type = (data.get("delivery_type") or "").strip().upper()
    delivery_address = (data.get("delivery_address") or "").strip() or None
    price = data.get("price")

    if delivery_type and delivery_type not in {"OFFICE", "ADDRESS"}:
        return api_error("delivery_type must be OFFICE or ADDRESS")

    # Build dynamic update
    fields = []
    params: List[Any] = []

    if weight is not None:
        fields.append("weight=%s")
        params.append(weight)
    if delivery_type:
        fields.append("delivery_type=%s")
        params.append(delivery_type)
    if "delivery_address" in data:
        fields.append("delivery_address=%s")
        params.append(delivery_address)
    if price is not None:
        fields.append("price=%s")
        params.append(price)

    if not fields:
        return api_error("No fields to update")

    params.append(shipment_id)

    res = db_execute(
        f"UPDATE shipments SET {', '.join(fields)} WHERE id=%s",
        tuple(params),
    )
    if res["affected"] == 0:
        return api_error("Shipment not found", 404)
    return jsonify(res)


@app.route("/api/shipments/<int:shipment_id>/status", methods=["PATCH"])
def shipments_set_status(shipment_id: int):
    guard = require_login()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().upper()

    if status not in {"SENT", "RECEIVED"}:
        return api_error("status must be SENT or RECEIVED")

    if status == "RECEIVED":
        res = db_execute(
            "UPDATE shipments SET status='RECEIVED', received_at=NOW() WHERE id=%s",
            (shipment_id,),
        )
    else:
        # SENT -> clear received_at
        res = db_execute(
            "UPDATE shipments SET status='SENT', received_at=NULL WHERE id=%s",
            (shipment_id,),
        )

    if res["affected"] == 0:
        return api_error("Shipment not found", 404)
    return jsonify(res)


# ----------------------------
# Reports / справки
# ----------------------------
@app.route("/api/reports/shipments/by-client/<int:client_id>", methods=["GET"])
def report_shipments_by_client(client_id: int):
    rows = db_query(
        """
        SELECT
          s.id,
          sc.name AS sender_name,
          rc.name AS receiver_name,
          s.weight, s.delivery_type, s.delivery_address,
          s.price, s.status, s.created_at, s.received_at
        FROM shipments s
        JOIN clients sc ON sc.id = s.sender_client_id
        JOIN clients rc ON rc.id = s.receiver_client_id
        WHERE s.sender_client_id=%s OR s.receiver_client_id=%s
        ORDER BY s.id DESC
        """,
        (client_id, client_id),
    )
    return jsonify(rows)


@app.route("/api/reports/shipments/by-employee/<int:employee_id>", methods=["GET"])
def report_shipments_by_employee(employee_id: int):
    rows = db_query(
        """
        SELECT
          s.id,
          sc.name AS sender_name,
          rc.name AS receiver_name,
          s.weight, s.delivery_type, s.delivery_address,
          s.price, s.status, s.created_at, s.received_at
        FROM shipments s
        JOIN clients sc ON sc.id = s.sender_client_id
        JOIN clients rc ON rc.id = s.receiver_client_id
        WHERE s.registered_by_employee_id=%s
        ORDER BY s.id DESC
        """,
        (employee_id,),
    )
    return jsonify(rows)


@app.route("/api/reports/revenue", methods=["GET"])
def report_revenue():
    """
    Query params:
      - from=YYYY-MM-DD (or ISO)
      - to=YYYY-MM-DD (or ISO)
    """
    from_raw = request.args.get("from", "")
    to_raw = request.args.get("to", "")

    date_from = parse_date(from_raw)
    date_to = parse_date(to_raw)

    if not date_from or not date_to:
        return api_error("from and to are required in format YYYY-MM-DD (or ISO)")

    row = db_query(
        """
        SELECT
          SUM(price) AS total_revenue,
          COUNT(*) AS shipments_count
        FROM shipments
        WHERE created_at BETWEEN %s AND %s
        """,
        (date_from, date_to),
        fetchone=True,
    )
    # In MySQL SUM can return None if no rows
    row["total_revenue"] = float(row["total_revenue"] or 0)
    return jsonify(row)


# ----------------------------
# Contact form (demo endpoint)
# ----------------------------
@app.route("/api/contact", methods=["POST"])
def contact_form():
    """Simple contact form endpoint (demo, doesn't persist to DB)."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not all([name, email, message]):
        return api_error("name, email, and message are required")

    # In a real app, you would save this to the database
    # For now, just log and return success
    print(f"Contact form: {name} ({email}) - {message}")

    return jsonify(
        {
            "message": "Благодарим ви! Съобщението беше успешно изпратено.",
            "received": {"name": name, "email": email, "message": message},
        }
    )


# ----------------------------
# Frontend routes (static)
# ----------------------------
@app.route("/")
def index():
    index_path = os.path.join(FRONTEND_DIR, "logistics-company.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, "logistics-company.html")
    return "Frontend not found. Place files in the frontend/ folder.", 404


@app.route("/<path:filename>")
def static_files(filename: str):
    # Prevent accidental capture of /api/* by this catch-all route
    if filename.startswith("api/") or filename == "api":
        return api_error("Not found", 404)

    return send_from_directory(FRONTEND_DIR, filename)


# ----------------------------
# Error handlers
# ----------------------------
@app.errorhandler(404)
def not_found(_):
    return api_error("Not found", 404)


@app.errorhandler(500)
def server_error(e):
    # In debug, Flask will show full stack anyway
    return api_error("Server error", 500)


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=(os.getenv("FLASK_DEBUG", "1") == "1"),
    )
