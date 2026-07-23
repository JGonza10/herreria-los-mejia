import os
import uuid
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import Producto, Cotizacion, Proyecto, Usuario, ESTADOS_PROYECTO
from auth import requiere_rol

admin_bp = Blueprint("admin", __name__)

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}


def extension_permitida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


# ---------- Catálogo (con imágenes) ----------

@admin_bp.get("/productos")
@requiere_rol("administrador")
def listar_productos_admin():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return jsonify([p.to_dict() for p in productos])


@admin_bp.post("/productos")
@requiere_rol("administrador")
def crear_producto():
    # multipart/form-data: campos de texto + archivo "imagen" opcional
    nombre = request.form.get("nombre", "").strip()
    material = request.form.get("material", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio_referencia_m2")
    destacado = request.form.get("destacado") == "true"

    if not nombre or not material or not precio:
        return jsonify({"error": "nombre, material y precio_referencia_m2 son obligatorios."}), 400

    producto = Producto(
        nombre=nombre,
        material=material,
        descripcion=descripcion,
        precio_referencia_m2=float(precio),
        destacado=destacado,
    )

    archivo = request.files.get("imagen")
    if archivo and archivo.filename and extension_permitida(archivo.filename):
        producto.imagen_url = guardar_imagen(archivo)

    db.session.add(producto)
    db.session.commit()
    return jsonify(producto.to_dict()), 201


@admin_bp.put("/productos/<int:producto_id>")
@requiere_rol("administrador")
def actualizar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    producto.nombre = request.form.get("nombre", producto.nombre)
    producto.material = request.form.get("material", producto.material)
    producto.descripcion = request.form.get("descripcion", producto.descripcion)
    if request.form.get("precio_referencia_m2"):
        producto.precio_referencia_m2 = float(request.form["precio_referencia_m2"])
    if "destacado" in request.form:
        producto.destacado = request.form.get("destacado") == "true"
    if "activo" in request.form:
        producto.activo = request.form.get("activo") == "true"

    archivo = request.files.get("imagen")
    if archivo and archivo.filename and extension_permitida(archivo.filename):
        producto.imagen_url = guardar_imagen(archivo)

    db.session.commit()
    return jsonify(producto.to_dict())


@admin_bp.delete("/productos/<int:producto_id>")
@requiere_rol("administrador")
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    return jsonify({"ok": True})


def guardar_imagen(archivo):
    carpeta = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(carpeta, exist_ok=True)
    nombre_seguro = secure_filename(archivo.filename)
    nombre_unico = f"{uuid.uuid4().hex}_{nombre_seguro}"
    archivo.save(os.path.join(carpeta, nombre_unico))
    return f"/uploads/{nombre_unico}"


# ---------- Cotizaciones ----------

@admin_bp.get("/cotizaciones")
@requiere_rol("administrador")
def listar_cotizaciones():
    cotizaciones = Cotizacion.query.order_by(Cotizacion.creado_en.desc()).all()
    return jsonify([c.to_dict() for c in cotizaciones])


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/aprobar")
@requiere_rol("administrador")
def aprobar_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    if cotizacion.proyecto:
        return jsonify({"error": "Esta cotización ya tiene un proyecto asociado."}), 400

    data = request.get_json(silent=True) or {}
    trabajador_id = data.get("trabajador_id")

    titulo = cotizacion.producto.nombre if cotizacion.producto else f"Proyecto {cotizacion.material} a medida"
    proyecto = Proyecto(
        cotizacion_id=cotizacion.id,
        cliente_id=cotizacion.cliente_id,
        trabajador_id=trabajador_id,
        titulo=titulo,
    )
    cotizacion.estado = "aprobada"
    db.session.add(proyecto)
    db.session.commit()
    return jsonify(proyecto.to_dict()), 201


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/rechazar")
@requiere_rol("administrador")
def rechazar_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    cotizacion.estado = "rechazada"
    db.session.commit()
    return jsonify(cotizacion.to_dict())


# ---------- Proyectos (dashboard de pedidos) ----------

@admin_bp.get("/proyectos")
@requiere_rol("administrador")
def listar_proyectos_admin():
    proyectos = Proyecto.query.order_by(Proyecto.creado_en.desc()).all()
    return jsonify([p.to_dict() for p in proyectos])


@admin_bp.put("/proyectos/<int:proyecto_id>")
@requiere_rol("administrador")
def actualizar_proyecto_admin(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    data = request.get_json(force=True)

    if "trabajador_id" in data:
        proyecto.trabajador_id = data["trabajador_id"]
    if "estado" in data and data["estado"] in ESTADOS_PROYECTO:
        proyecto.estado = data["estado"]
    if "avance_porcentaje" in data:
        proyecto.avance_porcentaje = max(0, min(100, int(data["avance_porcentaje"])))
    if "notas_internas" in data:
        proyecto.notas_internas = data["notas_internas"]

    db.session.commit()
    return jsonify(proyecto.to_dict())


# ---------- Usuarios (crear cuentas de trabajador) ----------

@admin_bp.get("/usuarios")
@requiere_rol("administrador")
def listar_usuarios():
    rol = request.args.get("rol")
    query = Usuario.query
    if rol:
        query = query.filter_by(rol=rol)
    usuarios = query.order_by(Usuario.nombre.asc()).all()
    return jsonify([u.to_dict() for u in usuarios])


@admin_bp.post("/usuarios")
@requiere_rol("administrador")
def crear_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    rol = data.get("rol", "trabajador")

    if not nombre or not email or not password:
        return jsonify({"error": "nombre, email y password son obligatorios."}), 400
    if rol not in ("administrador", "trabajador"):
        return jsonify({"error": "Desde este panel solo se crean cuentas de administrador o trabajador."}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    usuario = Usuario(nombre=nombre, email=email, telefono=data.get("telefono", ""), rol=rol)
    usuario.set_password(password)
    db.session.add(usuario)
    db.session.commit()
    return jsonify(usuario.to_dict()), 201
