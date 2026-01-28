from flask import Blueprint, request, jsonify
from extensions import db
from models.shipment import Shipment
from models.client import Client
from models.employee import Employee
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from sqlalchemy import and_, or_, func

shipment_bp = Blueprint("shipment", __name__, url_prefix="/api/shipment")

# REQUIREMENT 3e: Shipment CRUD operations (Create, Read, Update, Delete)
# REQUIREMENT 4: Employees register shipments (sent and received)
# REQUIREMENT 6: Employees see all shipments
# REQUIREMENT 7: Clients see their own shipments (sent or received)

@shipment_bp.get("")
@jwt_required()
def get_shipments():
    """
    REQUIREMENT 6: Employees can view all shipments
    REQUIREMENT 7: Clients can only view their own shipments (sent or received)
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    if role == "EMPLOYEE":
        # REQUIREMENT 6: Employees see all shipments
        shipments = Shipment.query.all()
    else:  # CLIENT
        # REQUIREMENT 7: Clients see only their own shipments (sender or receiver)
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
    REQUIREMENT 3e: Get specific shipment details
    REQUIREMENT 6: Employees can view any shipment
    REQUIREMENT 7: Clients can only view their own shipments
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    if role == "CLIENT":
        # REQUIREMENT 7: Verify client owns the shipment
        client = Client.query.filter_by(user_id=user_id).first()
        if client.id != shipment.sender_id and client.id != shipment.receiver_id:
            return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify(shipment.to_dict()), 200

@shipment_bp.post("")
@jwt_required()
def create_shipment():
    """
    REQUIREMENT 3e: Create new shipment (CRUD - Create)
    REQUIREMENT 4: Employees and clients can create shipments
    """
    claims = get_jwt()
    user_id = claims.get("sub")
    role = claims.get("role")
    
    data = request.get_json() or {}
    
    required_fields = ["sender_id", "receiver_id", "tracking_number", 
                      "weight", "dimensions", "description", "price", "origin_address", "destination_address"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": f"Required fields: {', '.join(required_fields)}"}), 400
    
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
    
    # REQUIREMENT 4: Create shipment with tracking information
    shipment = Shipment(
        sender_id=data.get("sender_id"),
        receiver_id=data.get("receiver_id"),
        registered_by_employee_id=registered_by_employee_id,
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
    """
    REQUIREMENT 3e: Update shipment details (CRUD - Update)
    REQUIREMENT 4: Employees can update shipment status and received date
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    shipment = Shipment.query.get(shipment_id)
    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404
    
    data = request.get_json() or {}
    
    # REQUIREMENT 4: Update delivery status
    if data.get("status"):
        shipment.status = data.get("status")
    # REQUIREMENT 4: Mark shipment as received with date
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
    """
    REQUIREMENT 3e: Delete shipment (CRUD - Delete)
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

# REQUIREMENT 5: REPORTING AND QUERIES

@shipment_bp.get("/reports/all-shipments")
@jwt_required()
def report_all_shipments():
    """
    REQUIREMENT 5c: Report all registered shipments
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
    REQUIREMENT 5d: Report all shipments registered by specific employee
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
    REQUIREMENT 5e: Report all shipments sent but not yet received (undelivered)
    Only employees can view this report
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    # REQUIREMENT 5e: Sent but not received (exclude cancelled)
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
    REQUIREMENT 5f: Report all shipments sent by specific client
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
    
    # REQUIREMENT 5f: Filter by sender (client who sent the shipment)
    shipments = Shipment.query.filter_by(sender_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/by-receiver/<int:client_id>")
@jwt_required()
def report_shipments_by_receiver(client_id):
    """
    REQUIREMENT 5g: Report all shipments received by specific client
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
    
    # REQUIREMENT 5g: Filter by receiver (client who received the shipment)
    shipments = Shipment.query.filter_by(receiver_id=client_id).all()
    return jsonify([s.to_dict() for s in shipments]), 200

@shipment_bp.get("/reports/revenue")
@jwt_required()
def report_company_revenue():
    """
    REQUIREMENT 5h: Report total revenue for company for specified time period
    Only employees can view this report
    Calculates revenue from all delivered shipments in the time range
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    # REQUIREMENT 5h: Filter by date range
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
