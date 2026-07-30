from flask import Blueprint, jsonify, request
from extensions import db
from models import Usuario
from auth import usuario_actual, generar_token, requiere_login

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

    token = generar_token(usuario)
    return jsonify({**usuario.to_dict(), "token": token}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.check_password(password) or not usuario.activo:
        return jsonify({"error": "Email o contraseña incorrectos."}), 401

    token = generar_token(usuario)
    return jsonify({**usuario.to_dict(), "token": token})


@auth_bp.post("/logout")
def logout():
    # El token es sin estado: "cerrar sesión" consiste en que el frontend lo
    # borre de su almacenamiento local. No hay nada que invalidar aquí.
    return jsonify({"ok": True})


@auth_bp.get("/yo")
def yo():
    usuario = usuario_actual()
    if not usuario:
        return jsonify({"usuario": None})
    return jsonify({"usuario": usuario.to_dict()})


@auth_bp.post("/password")
@requiere_login
def cambiar_password():
    """Cambia la contraseña del usuario logueado. Sube su token_version, así
    que cualquier otra sesión abierta (otro navegador, un token robado)
    queda invalidada de inmediato."""
    usuario = usuario_actual()
    data = request.get_json(force=True)
    password_actual = data.get("password_actual", "")
    password_nueva = data.get("password_nueva", "")

    if not usuario.check_password(password_actual):
        return jsonify({"error": "La contraseña actual no es correcta."}), 401
    if len(password_nueva) < 6:
        return jsonify({"error": "La contraseña nueva debe tener al menos 6 caracteres."}), 400

    usuario.set_password(password_nueva)
    usuario.token_version += 1
    db.session.commit()

    token = generar_token(usuario)
    return jsonify({"ok": True, "token": token})
