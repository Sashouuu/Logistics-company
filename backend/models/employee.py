from extensions import db
from datetime import datetime

# Employee role with company and office assignment
# Employee data management (CRUD operations)
class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.id"), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user = db.relationship("User", backref="employee_profile")
    #  Employees register shipments
    shipments_registered = db.relationship("Shipment", backref="registered_by_employee", foreign_keys="Shipment.registered_by_employee_id")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "office_id": self.office_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "is_active": self.is_active,
        }
