from flask import Blueprint, request, jsonify
from extensions import db
from models.office import Office
from flask_jwt_extended import jwt_required, get_jwt

office_bp = Blueprint("office", __name__, url_prefix="/api/office")

# Office CRUD operations (Create, Read, Update, Delete)

@office_bp.get("")
@jwt_required()
def get_offices():
    """
    Get all offices (Read)
    Only employees can view offices
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    company_id = request.args.get("company_id")
    if company_id:
        # Filter offices by company
        offices = Office.query.filter_by(company_id=company_id).all()
    else:
        offices = Office.query.all()
    
    return jsonify([o.to_dict() for o in offices]), 200

@office_bp.get("/<int:office_id>")
@jwt_required()
def get_office(office_id):
    """
    Get specific office details (Read)
    """
    office = Office.query.get(office_id)
    if not office:
        return jsonify({"error": "Office not found"}), 404
    
    return jsonify(office.to_dict()), 200

@office_bp.post("")
@jwt_required()
def create_office():
    """
    Create new office (CRUD - Create)
    Only employees can create offices
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() or {}
    
    required_fields = ["name", "company_id", "address", "phone", "email", "city", "country"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": f"Required fields: {', '.join(required_fields)}"}), 400
    
    office = Office(
        name=data.get("name"),
        company_id=data.get("company_id"),
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email"),
        city=data.get("city"),
        country=data.get("country"),
    )
    
    try:
        db.session.add(office)
        db.session.commit()
        return jsonify({"message": "Office created", "office_id": office.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@office_bp.put("/<int:office_id>")
@jwt_required()
def update_office(office_id):
    """
    Update office details (CRUD - Update)
    Only employees can update offices
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    office = Office.query.get(office_id)
    if not office:
        return jsonify({"error": "Office not found"}), 404
    
    data = request.get_json() or {}
    
    office.name = data.get("name", office.name)
    office.address = data.get("address", office.address)
    office.phone = data.get("phone", office.phone)
    office.email = data.get("email", office.email)
    office.city = data.get("city", office.city)
    office.country = data.get("country", office.country)
    
    try:
        db.session.commit()
        return jsonify({"message": "Office updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@office_bp.delete("/<int:office_id>")
@jwt_required()
def delete_office(office_id):
    """
    Delete office (CRUD - Delete)
    Only employees can delete offices
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    office = Office.query.get(office_id)
    if not office:
        return jsonify({"error": "Office not found"}), 404
    
    try:
        db.session.delete(office)
        db.session.commit()
        return jsonify({"message": "Office deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
