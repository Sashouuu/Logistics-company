from .contact import bp as contact_bp

def register_routes(app):
    app.register_blueprint(contact_bp)
