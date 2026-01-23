from flask import Blueprint, request, jsonify

bp = Blueprint("contact", __name__)

@bp.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"error": "Моля попълнете име, имейл и съобщение."}), 400

    # Засега само връщаме успех (по-късно може да записваме в DB таблица contact_messages)
    return jsonify({"message": "Съобщението беше получено. Благодарим!"}), 200
