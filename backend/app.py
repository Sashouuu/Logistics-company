from flask import Flask, jsonify, render_template
from config import Config
from extensions import db, migrate, jwt
from routes import register_routes


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

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
