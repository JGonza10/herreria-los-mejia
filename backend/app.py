import os
from flask import Flask
from flask_cors import CORS

from extensions import db
from routes.catalogo import catalogo_bp
from routes.cotizador import cotizador_bp
from routes.chatbot import chatbot_bp


def create_app():
    app = Flask(__name__)

    db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    # Railway entrega postgres:// pero SQLAlchemy 1.4+ requiere postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(catalogo_bp, url_prefix="/api/catalogo")
    app.register_blueprint(cotizador_bp, url_prefix="/api/cotizador")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

    @app.get("/api/salud")
    def salud():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
