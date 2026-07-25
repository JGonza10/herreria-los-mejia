from functools import wraps
from flask import request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import Usuario

# Duración del token: 30 días. Como el frontend y el backend viven en
# dominios distintos de Railway, los navegadores (Chrome, Safari, Firefox)
# bloquean la cookie de sesión por ser "de terceros" (cross-site), sin
# importar que SameSite=None/Secure estén bien puestos. Por eso la sesión
# ya NO se maneja con cookie: el login regresa un token firmado que el
# frontend guarda (localStorage) y manda en cada petición como
# "Authorization: Bearer <token>". Esto funciona igual sin importar el
# dominio, porque no depende de políticas de cookies del navegador.
TOKEN_MAX_AGE = 60 * 60 * 24 * 30


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth-token")


def generar_token(usuario_id):
    return _serializer().dumps({"user_id": usuario_id})


def _token_de_request():
    encabezado = request.headers.get("Authorization", "")
    if encabezado.startswith("Bearer "):
        return encabezado[len("Bearer "):].strip()
    return None


def usuario_actual():
    token = _token_de_request()
    if not token:
        return None
    try:
        datos = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return Usuario.query.get(datos.get("user_id"))


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
