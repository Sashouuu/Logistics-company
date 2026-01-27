from flask import Flask, jsonify, render_template
from config import Config
from extensions import db, migrate, jwt
from routes import register_routes
import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Routes
    register_routes(app)

    @app.get("/")
    def home():
        return render_template("logistics-company.html")

    @app.get("/login.html")
    def login():
        return render_template("login.html")

    @app.get("/register.html")
    def register():
        return render_template("register.html")

    @app.get("/shipments.html")
    def shipments():
        return render_template("shipments.html")

    @app.get("/dashboard.html")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
