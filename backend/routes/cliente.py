from flask import Blueprint, jsonify
from models import Cotizacion, Proyecto
from auth import requiere_rol, usuario_actual

cliente_bp = Blueprint("cliente", __name__)


@cliente_bp.get("/cotizaciones")
@requiere_rol("cliente")
def mis_cotizaciones():
    user = usuario_actual()
    cotizaciones = (
        Cotizacion.query.filter_by(cliente_id=user.id)
        .order_by(Cotizacion.creado_en.desc())
        .all()
    )
    return jsonify([c.to_dict() for c in cotizaciones])


@cliente_bp.get("/proyectos")
@requiere_rol("cliente")
def mis_proyectos():
    user = usuario_actual()
    proyectos = (
        Proyecto.query.filter_by(cliente_id=user.id)
        .order_by(Proyecto.creado_en.desc())
        .all()
    )
    return jsonify([p.to_dict(vista="cliente") for p in proyectos])
