from flask import Blueprint, jsonify, request
from extensions import db
from models import Proyecto
from auth import requiere_rol, usuario_actual

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
    return jsonify([p.to_dict() for p in proyectos])


@trabajador_bp.get("/proyectos/pendientes")
@requiere_rol("trabajador")
def proyectos_pendientes_sin_asignar():
    """Solo lectura: para que el trabajador vea qué hay en la cola general."""
    proyectos = (
        Proyecto.query.filter_by(trabajador_id=None, estado="pendiente")
        .order_by(Proyecto.creado_en.asc())
        .all()
    )
    return jsonify([p.to_dict() for p in proyectos])


@trabajador_bp.put("/proyectos/<int:proyecto_id>/avance")
@requiere_rol("trabajador")
def actualizar_avance(proyecto_id):
    user = usuario_actual()
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    if proyecto.trabajador_id != user.id:
        return jsonify({"error": "Este proyecto no está asignado a ti."}), 403

    data = request.get_json(force=True)
    if "avance_porcentaje" in data:
        proyecto.avance_porcentaje = max(0, min(100, int(data["avance_porcentaje"])))
    if "estado" in data and data["estado"] in ("en_proceso", "terminado"):
        proyecto.estado = data["estado"]
    if "notas_internas" in data:
        proyecto.notas_internas = data["notas_internas"]

    db.session.commit()
    return jsonify(proyecto.to_dict())
