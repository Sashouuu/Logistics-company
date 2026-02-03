from flask import Blueprint, request, jsonify
from extensions import db
from models.client import Client
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt

client_bp = Blueprint("client", __name__, url_prefix="/api/client")

# Client CRUD operations (Create, Read, Update, Delete)
# Report all clients

@client_bp.get("")
@jwt_required()
def get_clients():
    """
    Get all clients (Read)
    Report all clients for employees
    Employees see all clients, clients see others for selecting recipients
    """
    claims = get_jwt()
    role = claims.get("role")
    user_id = claims.get("sub")  # This is the user_id as integer or string
    
    if role == "EMPLOYEE":
        # Employees can view all clients
        clients = Client.query.all()
    else:
        # Clients see all other clients (excluding themselves)
        # Convert user_id to int if needed for comparison
        try:
            user_id_int = int(user_id) if user_id else None
            if user_id_int:
                clients = Client.query.filter(Client.user_id != user_id_int).all()
            else:
                clients = []
        except (ValueError, TypeError):
            clients = []
    
    return jsonify([c.to_dict() for c in clients]), 200

@client_bp.get("/me")
@jwt_required()
def get_current_client():
    """Get current logged-in client's profile"""
    claims = get_jwt()
    role = claims.get("role")
    user_id = claims.get("sub")
    
    if role != "CLIENT":
        return jsonify({"error": "Only clients can access this endpoint"}), 403
    
    try:
        user_id_int = int(user_id) if user_id else None
        if not user_id_int:
            return jsonify({"error": "Invalid user ID"}), 400
        
        client = Client.query.filter_by(user_id=user_id_int).first()
        if not client:
            return jsonify({"error": "Client profile not found"}), 404
        
        return jsonify(client.to_dict()), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user ID"}), 400

@client_bp.get("/<int:client_id>")
@jwt_required()
def get_client(client_id):
    """
    Get specific client details (Read)
    """
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    return jsonify(client.to_dict()), 200

@client_bp.post("")
@jwt_required()
def create_client():
    """
    Create new client (CRUD - Create)
    Only employees can create new client records
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() or {}
    
    required_fields = ["user_id", "company_name", "first_name", "last_name", "phone", "address", "city", "country"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": f"Required fields: {', '.join(required_fields)}"}), 400
    
    if not User.query.get(data.get("user_id")):
        return jsonify({"error": "User not found"}), 404
    
    if Client.query.filter_by(user_id=data.get("user_id")).first():
        return jsonify({"error": "User is already a client"}), 400
    
    client = Client(
        user_id=data.get("user_id"),
        company_name=data.get("company_name"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        address=data.get("address"),
        city=data.get("city"),
        country=data.get("country"),
    )
    
    try:
        db.session.add(client)
        db.session.commit()
        return jsonify({"message": "Client created", "client_id": client.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@client_bp.put("/<int:client_id>")
@jwt_required()
def update_client(client_id):
    """
    Update client details (CRUD - Update)
    Employees can update any client, clients can update their own profile
    """
    claims = get_jwt()
    role = claims.get("role")
    user_id = claims.get("sub")
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    # Authorization - clients can only update their own data
    if role == "CLIENT":
        try:
            user_id_int = int(user_id) if user_id else None
            if client.user_id != user_id_int:
                return jsonify({"error": "Unauthorized"}), 403
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user ID"}), 400
    
    data = request.get_json() or {}
    
    client.company_name = data.get("company_name", client.company_name)
    client.first_name = data.get("first_name", client.first_name)
    client.last_name = data.get("last_name", client.last_name)
    client.phone = data.get("phone", client.phone)
    client.address = data.get("address", client.address)
    client.city = data.get("city", client.city)
    client.country = data.get("country", client.country)
    if "is_active" in data:
        client.is_active = data.get("is_active")
    
    try:
        db.session.commit()
        return jsonify({"message": "Client updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@client_bp.delete("/<int:client_id>")
@jwt_required()
def delete_client(client_id):
    """
    Delete client (CRUD - Delete)
    Only employees can delete clients
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    try:
        db.session.delete(client)
        db.session.commit()
        return jsonify({"message": "Client deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
