from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# User registration and login
# Role assignment (CLIENT or EMPLOYEE)
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Role assignment (CLIENT or EMPLOYEE)
    role = db.Column(db.String(20), nullable=False)  # CLIENT or EMPLOYEE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        # Secure password hashing for registration
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Password verification during login
        return check_password_hash(self.password_hash, password)

