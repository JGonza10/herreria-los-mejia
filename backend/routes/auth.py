from flask import Blueprint, jsonify, request, session
from extensions import db
from models import Usuario
from auth import usuario_actual, requiere_login

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/registro")
def registro():
    """Registro público — siempre crea cuentas de rol 'cliente'.
    Las cuentas de administrador/trabajador las crea un administrador
    desde el panel (ver routes/admin.py)."""
    data = request.get_json(force=True)
    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip().lower()
    telefono = data.get("telefono", "").strip()
    password = data.get("password", "")

    if not nombre or not email or not password:
        return jsonify({"error": "Nombre, email y contraseña son obligatorios."}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres."}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    usuario = Usuario(nombre=nombre, email=email, telefono=telefono, rol="cliente")
    usuario.set_password(password)
    db.session.add(usuario)
    db.session.commit()

    session["user_id"] = usuario.id
    return jsonify(usuario.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.check_password(password) or not usuario.activo:
        return jsonify({"error": "Email o contraseña incorrectos."}), 401

    session["user_id"] = usuario.id
    return jsonify(usuario.to_dict())


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"ok": True})


@auth_bp.get("/yo")
def yo():
    usuario = usuario_actual()
    if not usuario:
        return jsonify({"usuario": None})
    return jsonify({"usuario": usuario.to_dict()})
