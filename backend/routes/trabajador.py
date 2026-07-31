from datetime import date, datetime
from flask import Blueprint, jsonify, request
from extensions import db
from models import FotoAvance, Proyecto, RegistroHoras, registrar_bitacora
from auth import requiere_rol, usuario_actual
from validacion import numero
from routes.admin import extension_permitida, guardar_imagen

trabajador_bp = Blueprint("trabajador", __name__)


@trabajador_bp.get("/proyectos/asignados")
@requiere_rol("trabajador")
def mis_proyectos():
    user = usuario_actual()
    proyectos = (
        Proyecto.query.filter_by(trabajador_id=user.id)
        .order_by(Proyecto.creado_en.desc())
        .all()
    )
    return jsonify([p.to_dict(vista="trabajador") for p in proyectos])


@trabajador_bp.get("/proyectos/pendientes")
@requiere_rol("trabajador")
def proyectos_pendientes_sin_asignar():
    """Solo lectura: para que el trabajador vea qué hay en la cola general."""
    proyectos = (
        Proyecto.query.filter_by(trabajador_id=None, estado="pendiente")
        .order_by(Proyecto.creado_en.asc())
        .all()
    )
    return jsonify([p.to_dict(vista="trabajador") for p in proyectos])


@trabajador_bp.put("/proyectos/<int:proyecto_id>/avance")
@requiere_rol("trabajador")
def actualizar_avance(proyecto_id):
    user = usuario_actual()
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    if proyecto.trabajador_id != user.id:
        return jsonify({"error": "Este proyecto no está asignado a ti."}), 403

    data = request.get_json(force=True)
    if "avance_porcentaje" in data:
        proyecto.avance_porcentaje = max(0, min(100, int(numero(data["avance_porcentaje"], "avance_porcentaje", minimo=0, maximo=100))))
    if "estado" in data and data["estado"] in ("en_proceso", "terminado") and data["estado"] != proyecto.estado:
        # Misma regla que en el panel de admin (Fase 7.2): sin anticipo
        # registrado, no se pasa a "en_proceso".
        if data["estado"] == "en_proceso" and not proyecto.pagos:
            return jsonify({"error": "Este proyecto no tiene ningún pago registrado. Pídele al administrador que registre el anticipo."}), 400
        registrar_bitacora(user.id, "proyecto", proyecto.id, "cambio_estado",
                            antes={"estado": proyecto.estado}, despues={"estado": data["estado"]})
        proyecto.estado = data["estado"]
    if "notas_internas" in data:
        proyecto.notas_internas = data["notas_internas"]

    db.session.commit()
    return jsonify(proyecto.to_dict(vista="trabajador"))


@trabajador_bp.post("/proyectos/<int:proyecto_id>/fotos")
@requiere_rol("trabajador")
def subir_foto_avance(proyecto_id):
    """Fotos de avance desde el teléfono (Fase 7.3) — reduce las llamadas
    de '¿cómo va mi portón?', que es tiempo del dueño convertido en tiempo
    de taller. La compresión del lado del cliente (canvas.toBlob calidad
    0.7) es responsabilidad del frontend; aquí solo se aplica el mismo
    límite de tamaño de petición de toda la app (MAX_CONTENT_LENGTH)."""
    user = usuario_actual()
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    if proyecto.trabajador_id != user.id:
        return jsonify({"error": "Este proyecto no está asignado a ti."}), 403

    archivo = request.files.get("imagen")
    if not archivo or not archivo.filename or not extension_permitida(archivo.filename):
        return jsonify({"error": "Falta una imagen válida (png, jpg, jpeg o webp)."}), 400

    foto = FotoAvance(
        proyecto_id=proyecto.id,
        url=guardar_imagen(archivo),
        subida_por_id=user.id,
        notas=request.form.get("notas"),
    )
    db.session.add(foto)
    db.session.commit()
    return jsonify(foto.to_dict()), 201


@trabajador_bp.post("/proyectos/<int:proyecto_id>/horas")
@requiere_rol("trabajador")
def registrar_horas(proyecto_id):
    """Horas por m² registradas por el trabajador (Fase 8.3) — para
    calibrar la mano de obra con datos en vez de con corazonada."""
    user = usuario_actual()
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    if proyecto.trabajador_id != user.id:
        return jsonify({"error": "Este proyecto no está asignado a ti."}), 403

    data = request.get_json(force=True)
    horas = numero(data.get("horas"), "horas", minimo=0.1, maximo=24)
    fecha_str = data.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else date.today()
    except ValueError:
        return jsonify({"error": "'fecha' debe tener formato AAAA-MM-DD."}), 400

    registro = RegistroHoras(
        proyecto_id=proyecto.id, trabajador_id=user.id,
        horas=horas, fecha=fecha, notas=data.get("notas"),
    )
    db.session.add(registro)
    db.session.commit()
    return jsonify(registro.to_dict()), 201
