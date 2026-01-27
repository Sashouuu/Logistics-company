from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User
from models.employee import Employee
from models.client import Client
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")
    role = data.get("role")  # CLIENT или EMPLOYEE

    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required"}), 400

    if role not in ["CLIENT", "EMPLOYEE"]:
        return jsonify({"error": "Role must be CLIENT or EMPLOYEE"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    user = User(email=email, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.flush()

        # Create additional profile based on role
        if role == "CLIENT":
            # Client registration requires company_name, first_name, last_name, phone, address, city, country
            client = Client(
                user_id=user.id,
                company_name=data.get("company_name", ""),
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                address=data.get("address", ""),
                city=data.get("city", ""),
                country=data.get("country", ""),
            )
            db.session.add(client)
        elif role == "EMPLOYEE":
            # Employee registration - company_id and office_id are optional for now
            company_id = data.get("company_id")
            office_id = data.get("office_id")
            
            # If both are provided, validate they exist
            if company_id and office_id:
                from models.company import Company
                from models.office import Office
                if not Company.query.get(company_id):
                    return jsonify({"error": "Company not found"}), 404
                if not Office.query.get(office_id):
                    return jsonify({"error": "Office not found"}), 404
                
                employee = Employee(
                    user_id=user.id,
                    company_id=company_id,
                    office_id=office_id,
                    first_name=data.get("first_name", ""),
                    last_name=data.get("last_name", ""),
                    phone=data.get("phone", ""),
                )
                db.session.add(employee)
            # If not provided, just create the user with EMPLOYEE role
            # They can complete their profile later

        db.session.commit()
        return jsonify({"message": "Registration successful", "user_id": user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({"access_token": token, "user_id": user.id, "role": user.role}), 200
