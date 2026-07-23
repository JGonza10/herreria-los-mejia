import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from extensions import db
from routes.catalogo import catalogo_bp
from routes.cotizador import cotizador_bp
from routes.chatbot import chatbot_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.trabajador import trabajador_bp
from routes.cliente import cliente_bp


def create_app():
    app = Flask(__name__)

    db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Sesión de login (cookie firmada). SECRET_KEY debe fijarse en producción
    # vía variable de entorno para que las sesiones no se invaliden en cada deploy.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar-en-produccion")
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RAILWAY_ENVIRONMENT") is not None

    # Carpeta donde se guardan las imágenes del catálogo.
    # NOTA: el disco de Railway es efímero salvo que agregues un Volume
    # montado en esta ruta — ver README, sección "Persistencia de imágenes".
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", os.path.join(app.root_path, "uploads"))
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "*")
    CORS(app, resources={r"/api/*": {"origins": frontend_origin}}, supports_credentials=True)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(catalogo_bp, url_prefix="/api/catalogo")
    app.register_blueprint(cotizador_bp, url_prefix="/api/cotizador")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(trabajador_bp, url_prefix="/api/trabajador")
    app.register_blueprint(cliente_bp, url_prefix="/api/cliente")

    @app.get("/api/salud")
    def salud():
        return {"status": "ok"}

    @app.get("/uploads/<path:nombre_archivo>")
    def servir_imagen(nombre_archivo):
        return send_from_directory(app.config["UPLOAD_FOLDER"], nombre_archivo)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
