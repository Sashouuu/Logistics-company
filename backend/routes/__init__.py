from .contact import bp as contact_bp
from .auth import auth_bp
from .company import company_bp
from .office import office_bp
from .employee import employee_bp
from .client import client_bp
from .shipment import shipment_bp

def register_routes(app):
    app.register_blueprint(contact_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(office_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(shipment_bp)
