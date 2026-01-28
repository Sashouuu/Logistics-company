from flask import Blueprint, request, jsonify
from extensions import db
from models.employee import Employee
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt

employee_bp = Blueprint("employee", __name__, url_prefix="/api/employee")

# REQUIREMENT 3b: Employee CRUD operations (Create, Read, Update, Delete)
# REQUIREMENT 5a: Report all employees

@employee_bp.get("")
@jwt_required()
def get_employees():
    """
    REQUIREMENT 3b: Get all employees (Read)
    REQUIREMENT 5a: Report all employees in the company
    Only employees can view this list
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    company_id = request.args.get("company_id")
    if company_id:
        # REQUIREMENT 5a: Filter by company
        employees = Employee.query.filter_by(company_id=company_id).all()
    else:
        employees = Employee.query.all()
    
    return jsonify([e.to_dict() for e in employees]), 200

@employee_bp.get("/<int:employee_id>")
@jwt_required()
def get_employee(employee_id):
    """
    REQUIREMENT 3b: Get specific employee details (Read)
    """
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    return jsonify(employee.to_dict()), 200

@employee_bp.post("")
@jwt_required()
def create_employee():
    """
    REQUIREMENT 3b: Create new employee (CRUD - Create)
    Only employees can create new employee records
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() or {}
    
    required_fields = ["user_id", "company_id", "office_id", "first_name", "last_name", "phone"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": f"Required fields: {', '.join(required_fields)}"}), 400
    
    if not User.query.get(data.get("user_id")):
        return jsonify({"error": "User not found"}), 404
    
    if Employee.query.filter_by(user_id=data.get("user_id")).first():
        return jsonify({"error": "User is already an employee"}), 400
    
    employee = Employee(
        user_id=data.get("user_id"),
        company_id=data.get("company_id"),
        office_id=data.get("office_id"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
    )
    
    try:
        db.session.add(employee)
        db.session.commit()
        return jsonify({"message": "Employee created", "employee_id": employee.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@employee_bp.put("/<int:employee_id>")
@jwt_required()
def update_employee(employee_id):
    """
    REQUIREMENT 3b: Update employee details (CRUD - Update)
    Only employees can update employee records
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    data = request.get_json() or {}
    
    employee.first_name = data.get("first_name", employee.first_name)
    employee.last_name = data.get("last_name", employee.last_name)
    employee.phone = data.get("phone", employee.phone)
    employee.office_id = data.get("office_id", employee.office_id)
    if "is_active" in data:
        employee.is_active = data.get("is_active")
    
    try:
        db.session.commit()
        return jsonify({"message": "Employee updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@employee_bp.delete("/<int:employee_id>")
@jwt_required()
def delete_employee(employee_id):
    """
    REQUIREMENT 3b: Delete employee (CRUD - Delete)
    Only employees can delete employee records
    """
    claims = get_jwt()
    if claims.get("role") != "EMPLOYEE":
        return jsonify({"error": "Unauthorized"}), 403
    
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({"message": "Employee deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
