from flask import Blueprint, request, jsonify
from extensions import db
from models.shipment import Shipment
from models.client import Client
from models.employee import Employee
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from sqlalchemy import and_, or_, func
from decimal import Decimal, InvalidOperation

shipment_bp = Blueprint("shipment", __name__, url_prefix="/api/shipment")


def _missing_required_fields(data, required_fields):
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
            continue
        value = data.get(field)
        # Allow 0 for numeric fields; reject None/empty strings.
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)
    return missing


def _parse_non_negative_float(value, field_name):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return parsed


def _parse_non_negative_decimal(value, field_name):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return parsed

# Shipment CRUD operations (Create, Read, Update, Delete)
# Employees register shipments (sent and received)
# Employees see all shipments
# Clients see their own shipments (sent or received)

@shipment_bp.get("")
@jwt_required()
def get_shipments():
    """
    Employees can view all shipments
    Clients can only view their own shipments (sent or received)
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    if role == "EMPLOYEE":
        # Employees see all shipments
        shipments = Shipment.query.all()
    else:  # CLIENT
        # Clients see only their own shipments (sender or receiver)
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
    """
    Get specific shipment details (Read)
    Employees can view any shipment
    Clients can only view their own shipments
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    if role == "CLIENT":
        # Clients can only view their own shipments
        client = Client.query.filter_by(user_id=user_id).first()
        if client.id != shipment.sender_id and client.id != shipment.receiver_id:
            return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify(shipment.to_dict()), 200

@shipment_bp.post("")
@jwt_required()
def create_shipment():
    """
    Create new shipment (CRUD - Create)
    Employees and clients can create shipments
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    data = request.get_json() or {}
    
    required_fields = ["sender_id", "receiver_id", "tracking_number", 
                      "weight", "dimensions", "description", "price", "origin_address", "destination_address"]
    missing = _missing_required_fields(data, required_fields)
    if missing:
        return jsonify({"error": f"Required fields: {', '.join(missing)}"}), 400

    # Validate numeric fields (prevents negative weight/price)
    try:
        weight = _parse_non_negative_float(data.get("weight"), "weight")
        price = _parse_non_negative_decimal(data.get("price"), "price")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    if Shipment.query.filter_by(tracking_number=data.get("tracking_number")).first():
        return jsonify({"error": "Tracking number already exists"}), 400
    
    # If client, verify they are the sender
    if role == "CLIENT":
        client = Client.query.filter_by(user_id=user_id).first()
        if not client or client.id != int(data.get("sender_id")):
            return jsonify({"error": "Clients can only send shipments as themselves"}), 403
        # For clients, find an employee to register the shipment
        employee = Employee.query.first()
        if not employee:
            return jsonify({"error": "No employee available to register shipment"}), 400
        registered_by_employee_id = employee.id
    else:
        # Employees must provide registered_by_employee_id
        if not data.get("registered_by_employee_id"):
            return jsonify({"error": "registered_by_employee_id required for employees"}), 400
        registered_by_employee_id = data.get("registered_by_employee_id")
    
    # Create shipment with tracking information
    shipment = Shipment(
        sender_id=data.get("sender_id"),
        receiver_id=data.get("receiver_id"),
        registered_by_employee_id=registered_by_employee_id,
        tracking_number=data.get("tracking_number"),
        weight=weight,
        dimensions=data.get("dimensions"),
        description=data.get("description"),
        price=price,
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
    """
    Update shipment details (CRUD - Update)
    Employees can update shipment status and received date
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    data = request.get_json() or {}
    
    # Update delivery status
    if data.get("status"):
        shipment.status = data.get("status")
    # Mark shipment as received with date
    if data.get("received_date") and data.get("status") == "DELIVERED":
        shipment.received_date = datetime.fromisoformat(data.get("received_date"))

    if "weight" in data:
        try:
            shipment.weight = _parse_non_negative_float(data.get("weight"), "weight")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

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
    """
    Delete shipment (CRUD - Delete)
    Only employees can delete shipments
    """
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

# REPORTING AND QUERIES

@shipment_bp.get("/reports/all-shipments")
@jwt_required()
def report_all_shipments():
    """
    Report all registered shipments
    Only employees can view this report
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-employee/<int:employee_id>")
@jwt_required()
def report_shipments_by_employee(employee_id):
    """
    Report all shipments registered by specific employee
    Only employees can view this report
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipments = Shipment.query.filter_by(registered_by_employee_id=employee_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/undelivered")
@jwt_required()
def report_undelivered_shipments():
    """
    Report all shipments sent but not yet received (undelivered)
    Only employees can view this report
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    # Sent but not received (exclude cancelled)
    shipments = Shipment.query.filter(
        Shipment.sent_date.isnot(None),
        Shipment.received_date.is_(None),
        Shipment.status != "CANCELLED",
    ).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-sender/<int:client_id>")
@jwt_required()
def report_shipments_by_sender(client_id):
    """
    Report all shipments sent by specific client
    Employees can view all, clients can only view their own
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    if role != "EMPLOYEE" and client.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Filter by sender (client who sent the shipment)
    shipments = Shipment.query.filter_by(sender_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-receiver/<int:client_id>")
@jwt_required()
def report_shipments_by_receiver(client_id):
    """
    Report all shipments received by specific client
    Employees can view all, clients can only view their own
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    if role != "EMPLOYEE" and client.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Filter by receiver (client who received the shipment)
    shipments = Shipment.query.filter_by(receiver_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/revenue")
@jwt_required()
def report_company_revenue():
    """
    Report total revenue for company for specified time period
    Only employees can view this report
    Calculates revenue from all delivered shipments in the time range
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    # Filter by date range
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    # Revenue is based on completed (DELIVERED) shipments.
    query = Shipment.query.filter(Shipment.status == "DELIVERED")
    if start_date:
        query = query.filter(Shipment.sent_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Shipment.sent_date <= datetime.fromisoformat(end_date))

    shipment_count = query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(Shipment.price), 0)).filter(
        Shipment.status == "DELIVERED",
        *( [Shipment.sent_date >= datetime.fromisoformat(start_date)] if start_date else [] ),
        *( [Shipment.sent_date <= datetime.fromisoformat(end_date)] if end_date else [] ),
    ).scalar()

    return jsonify({
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_revenue": str(total_revenue),
        "shipment_count": shipment_count
    }), 200
