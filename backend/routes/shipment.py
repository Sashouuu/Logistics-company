from flask import Blueprint, request, jsonify
from extensions import db
from models.shipment import Shipment
from models.client import Client
from models.employee import Employee
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from sqlalchemy import and_, or_

shipment_bp = Blueprint("shipment", __name__, url_prefix="/api/shipment")

@shipment_bp.get("")
@jwt_required()
def get_shipments():
    """Get shipments based on user role"""
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    if role == "EMPLOYEE":
        # Employees see all shipments
        shipments = Shipment.query.all()
    else:  # CLIENT
        # Clients see only their own shipments
        client = Client.query.filter_by(user_id=user_id).first()
        if not client:
            return jsonify({"error": "Client profile not found"}), 404
        
        shipments = Shipment.query.filter(
            or_(Shipment.sender_id == client.id, Shipment.receiver_id == client.id)
        ).all()
    
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/<int:shipment_id>")
@jwt_required()
def get_shipment(shipment_id):
    """Get a specific shipment"""
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    if role == "CLIENT":
        client = Client.query.filter_by(user_id=user_id).first()
        if client.id != shipment.sender_id and client.id != shipment.receiver_id:
            return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify(shipment.to_dict()), 200

@shipment_bp.post("")
@jwt_required()
def create_shipment():
    """Create a new shipment - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() or {}
    
    required_fields = ["sender_id", "receiver_id", "registered_by_employee_id", "tracking_number", 
                      "weight", "dimensions", "description", "price", "origin_address", "destination_address"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": f"Required fields: {', '.join(required_fields)}"}), 400
    
    if Shipment.query.filter_by(tracking_number=data.get("tracking_number")).first():
        return jsonify({"error": "Tracking number already exists"}), 400
    
    shipment = Shipment(
        sender_id=data.get("sender_id"),
        receiver_id=data.get("receiver_id"),
        registered_by_employee_id=data.get("registered_by_employee_id"),
        tracking_number=data.get("tracking_number"),
        weight=data.get("weight"),
        dimensions=data.get("dimensions"),
        description=data.get("description"),
        price=data.get("price"),
        sent_date=datetime.fromisoformat(data.get("sent_date")) if data.get("sent_date") else datetime.utcnow(),
        status=data.get("status", "PENDING"),
        origin_address=data.get("origin_address"),
        destination_address=data.get("destination_address"),
    )
    
    try:
        db.session.add(shipment)
        db.session.commit()
        return jsonify({"message": "Shipment created", "shipment_id": shipment.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@shipment_bp.put("/<int:shipment_id>")
@jwt_required()
def update_shipment(shipment_id):
    """Update a shipment - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    data = request.get_json() or {}
    
    if data.get("status"):
        shipment.status = data.get("status")
    if data.get("received_date") and data.get("status") == "DELIVERED":
        shipment.received_date = datetime.fromisoformat(data.get("received_date"))
    
    shipment.weight = data.get("weight", shipment.weight)
    shipment.dimensions = data.get("dimensions", shipment.dimensions)
    shipment.description = data.get("description", shipment.description)
    
    try:
        db.session.commit()
        return jsonify({"message": "Shipment updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@shipment_bp.delete("/<int:shipment_id>")
@jwt_required()
def delete_shipment(shipment_id):
    """Delete a shipment - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    try:
        db.session.delete(shipment)
        db.session.commit()
        return jsonify({"message": "Shipment deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# REPORTS / QUERIES

@shipment_bp.get("/reports/all-shipments")
@jwt_required()
def report_all_shipments():
    """Report: All registered shipments - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-employee/<int:employee_id>")
@jwt_required()
def report_shipments_by_employee(employee_id):
    """Report: Shipments registered by specific employee - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.filter_by(registered_by_employee_id=employee_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/undelivered")
@jwt_required()
def report_undelivered_shipments():
    """Report: All shipments sent but not received - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.filter(
        and_(Shipment.status != "DELIVERED", Shipment.status != "CANCELLED")
    ).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-sender/<int:client_id>")
@jwt_required()
def report_shipments_by_sender(client_id):
    """Report: Shipments sent by specific client - only for employees or the client"""
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    if role != "EMPLOYEE" and client.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.filter_by(sender_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-receiver/<int:client_id>")
@jwt_required()
def report_shipments_by_receiver(client_id):
    """Report: Shipments received by specific client - only for employees or the client"""
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    if role != "EMPLOYEE" and client.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.filter_by(receiver_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/revenue")
@jwt_required()
def report_company_revenue():
    """Report: Total revenue for a specific period - only for employees"""
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    query = Shipment.query
    if start_date:
        query = query.filter(Shipment.sent_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Shipment.sent_date <= datetime.fromisoformat(end_date))
    
    shipments = query.all()
    total_revenue = sum(float(s.price) for s in shipments)
    
    return jsonify({
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_revenue": total_revenue,
        "shipment_count": len(shipments)
    }), 200
