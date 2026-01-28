from extensions import db
from datetime import datetime
from decimal import Decimal

# REQUIREMENT 3e: Shipment data management (CRUD operations)
# REQUIREMENT 4: Employees register sent and received shipments
# REQUIREMENT 5a-h: Shipment tracking and reporting for various queries
# REQUIREMENT 6: Employees can see all shipments
# REQUIREMENT 7: Clients can see their shipments (sent or received)
class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(db.Integer, primary_key=True)
    # REQUIREMENT 4: Track sender (client)
    sender_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    # REQUIREMENT 4: Track receiver (client)
    receiver_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    # REQUIREMENT 4: Track which employee registered the shipment
    registered_by_employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    
    # Shipment details
    tracking_number = db.Column(db.String(50), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # kg
    dimensions = db.Column(db.String(100), nullable=False)  # e.g., "30x40x50"
    description = db.Column(db.Text, nullable=False)
    # REQUIREMENT 5h: Track price for revenue calculation
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Dates
    # REQUIREMENT 5e: Track sent date for undelivered shipments
    sent_date = db.Column(db.DateTime, nullable=False)
    # REQUIREMENT 5e: Track received date for delivery status
    received_date = db.Column(db.DateTime, nullable=True)
    
    # Status: PENDING, IN_TRANSIT, DELIVERED, CANCELLED
    # REQUIREMENT 5e: Status for tracking undelivered shipments
    status = db.Column(db.String(20), default="PENDING", nullable=False)
    
    # Origin and destination
    origin_address = db.Column(db.String(255), nullable=False)
    destination_address = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "registered_by_employee_id": self.registered_by_employee_id,
            "tracking_number": self.tracking_number,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "description": self.description,
            "price": str(self.price),
            "sent_date": self.sent_date.isoformat() if self.sent_date else None,
            "received_date": self.received_date.isoformat() if self.received_date else None,
            "status": self.status,
            "origin_address": self.origin_address,
            "destination_address": self.destination_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
