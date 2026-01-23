from .contact import bp as contact_bp
from .auth import auth_bp

def register_routes(app):
    app.register_blueprint(contact_bp)
    app.register_blueprint(auth_bp)
