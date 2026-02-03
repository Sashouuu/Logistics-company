from flask import Blueprint, request, jsonify
from extensions import db
from models.company import Company
from flask_jwt_extended import jwt_required, get_jwt

company_bp = Blueprint("company", __name__, url_prefix="/api/company")

# Company CRUD operations (Create, Read, Update, Delete)

@company_bp.get("")
@jwt_required()
def get_companies():
    """
    Get all companies (Read)
    Only employees can view companies
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    companies = Company.query.all()
    return jsonify([c.to_dict() for c in companies]), 200

@company_bp.get("/<int:company_id>")
@jwt_required()
def get_company(company_id):
    """
    Get specific company details (Read)
    """
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    return jsonify(company.to_dict()), 200

@company_bp.post("")
@jwt_required()
def create_company():
    """
    Create new company (CRUD - Create)
    Only employees can create companies
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() or {}
    
    if not data.get("name") or not data.get("registration_number"):
        return jsonify({"error": "Name and registration number are required"}), 400
    
    if Company.query.filter_by(name=data.get("name")).first():
        return jsonify({"error": "Company with this name already exists"}), 400
    
    company = Company(
        name=data.get("name"),
        registration_number=data.get("registration_number"),
        address=data.get("address", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
    )
    
    try:
        db.session.add(company)
        db.session.commit()
        return jsonify({"message": "Company created", "company_id": company.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@company_bp.put("/<int:company_id>")
@jwt_required()
def update_company(company_id):
    """
    Update company details (CRUD - Update)
    Only employees can update companies
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    data = request.get_json() or {}
    
    company.name = data.get("name", company.name)
    company.registration_number = data.get("registration_number", company.registration_number)
    company.address = data.get("address", company.address)
    company.phone = data.get("phone", company.phone)
    company.email = data.get("email", company.email)
    
    try:
        db.session.commit()
        return jsonify({"message": "Company updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@company_bp.delete("/<int:company_id>")
@jwt_required()
def delete_company(company_id):
    """
    Delete company (CRUD - Delete)
    Only employees can delete companies
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    try:
        db.session.delete(company)
        db.session.commit()
        return jsonify({"message": "Company deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
