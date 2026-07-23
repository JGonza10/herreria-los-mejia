from functools import wraps
from flask import session, jsonify
from models import Usuario


def usuario_actual():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return Usuario.query.get(user_id)


def requiere_login(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        user = usuario_actual()
        if not user or not user.activo:
            return jsonify({"error": "No autenticado."}), 401
        return f(*args, **kwargs)
    return envoltura


def requiere_rol(*roles_permitidos):
    def decorador(f):
        @wraps(f)
        def envoltura(*args, **kwargs):
            user = usuario_actual()
            if not user or not user.activo:
                return jsonify({"error": "No autenticado."}), 401
            if user.rol not in roles_permitidos:
                return jsonify({"error": "No tienes permiso para esta acción."}), 403
            return f(*args, **kwargs)
        return envoltura
    return decorador
