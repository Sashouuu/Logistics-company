from flask import Blueprint, request, jsonify
from extensions import db
from models.contact import Contact

bp = Blueprint("contact", __name__)

@bp.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"error": "Моля попълнете име, имейл и съобщение."}), 400

    contact_msg = Contact(
        name=name,
        email=email,
        message=message
    )
    
    try:
        db.session.add(contact_msg)
        db.session.commit()
        return jsonify({"message": "Съобщението беше получено. Благодарим!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
