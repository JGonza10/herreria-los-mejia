"""Administración de tarifas versionadas (Fase 4.2 de actualizar.md).

Hoy el cotizador sigue leyendo PrecioMaterial (routes/cotizador.py no ha
cambiado). Esto le da al administrador una pantalla real para crear y
versionar listas de precios — conectar calcular_precio() a la tarifa activa
en vez de a PrecioMaterial es el siguiente paso, no incluido todavía porque
depende de resolver cómo se cobra cada sistema (Fase 4.3).

Antes de esta pantalla, la única forma de cambiar un precio era editar
seed.py, hacer commit y redesplegar. Un dueño de taller no va a hacer eso.
"""
from datetime import date, datetime
from flask import Blueprint, jsonify, request
from extensions import db
from models import Tarifa, PrecioTarifa, registrar_bitacora
from auth import requiere_rol, usuario_actual
from validacion import numero

tarifas_bp = Blueprint("tarifas", __name__)


@tarifas_bp.get("")
@requiere_rol("administrador")
def listar_tarifas():
    tarifas = Tarifa.query.order_by(Tarifa.vigente_desde.desc()).all()
    return jsonify([t.to_dict() for t in tarifas])


@tarifas_bp.post("")
@requiere_rol("administrador")
def crear_tarifa():
    data = request.get_json(force=True)
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "'nombre' es obligatorio."}), 400

    try:
        vigente_desde = datetime.strptime(data.get("vigente_desde", ""), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "'vigente_desde' debe tener formato AAAA-MM-DD."}), 400

    tarifa = Tarifa(nombre=nombre, vigente_desde=vigente_desde, creada_por_id=usuario_actual().id)
    db.session.add(tarifa)
    db.session.commit()
    return jsonify(tarifa.to_dict()), 201


@tarifas_bp.get("/<int:tarifa_id>")
@requiere_rol("administrador")
def obtener_tarifa(tarifa_id):
    tarifa = Tarifa.query.get_or_404(tarifa_id)
    return jsonify(tarifa.to_dict(con_precios=True))


@tarifas_bp.put("/<int:tarifa_id>/precios")
@requiere_rol("administrador")
def reemplazar_precios(tarifa_id):
    """Reemplaza toda la lista de precios de la tarifa de una sola vez —
    así el formulario del admin manda la tabla completa después de editarla,
    sin tener que armar un endpoint por fila."""
    tarifa = Tarifa.query.get_or_404(tarifa_id)
    data = request.get_json(force=True)
    precios = data.get("precios")
    if not isinstance(precios, list):
        return jsonify({"error": "'precios' debe ser una lista."}), 400

    precios_antes = [p.to_dict() for p in tarifa.precios]
    nuevos = []
    for fila in precios:
        if not isinstance(fila, dict) or not fila.get("concepto") or not fila.get("clave") or not fila.get("unidad"):
            return jsonify({"error": "Cada precio necesita 'concepto', 'clave' y 'unidad'."}), 400
        nuevos.append(PrecioTarifa(
            tarifa_id=tarifa.id,
            tipo_trabajo_id=fila.get("tipo_trabajo_id"),
            concepto=fila["concepto"],
            clave=fila["clave"],
            unidad=fila["unidad"],
            precio=numero(fila.get("precio"), "precio", minimo=0),
        ))

    PrecioTarifa.query.filter_by(tarifa_id=tarifa.id).delete()
    db.session.add_all(nuevos)
    db.session.flush()  # para que los nuevos ya tengan id al registrarlos en la bitácora
    registrar_bitacora(usuario_actual().id, "tarifa", tarifa.id, "cambio_precio",
                        antes={"precios": precios_antes}, despues={"precios": [n.to_dict() for n in nuevos]})
    db.session.commit()
    return jsonify(tarifa.to_dict(con_precios=True))


@tarifas_bp.post("/<int:tarifa_id>/activar")
@requiere_rol("administrador")
def activar_tarifa(tarifa_id):
    tarifa = Tarifa.query.get_or_404(tarifa_id)
    anterior = Tarifa.query.filter_by(activa=True).first()
    Tarifa.query.update({Tarifa.activa: False})
    tarifa.activa = True
    registrar_bitacora(usuario_actual().id, "tarifa", tarifa.id, "activacion",
                        antes={"tarifa_activa_id": anterior.id if anterior else None}, despues={"tarifa_activa_id": tarifa.id})
    db.session.commit()
    return jsonify(tarifa.to_dict())


@tarifas_bp.post("/<int:tarifa_id>/duplicar")
@requiere_rol("administrador")
def duplicar_tarifa(tarifa_id):
    """Copiar una tarifa vigente como punto de partida de la nueva
    ('Copiar Julio 2026 a Agosto 2026 y subir todo 4%') — así es como
    realmente se actualiza una lista de precios."""
    origen = Tarifa.query.get_or_404(tarifa_id)
    data = request.get_json(force=True)
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "'nombre' es obligatorio."}), 400

    try:
        vigente_desde = datetime.strptime(data.get("vigente_desde", ""), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "'vigente_desde' debe tener formato AAAA-MM-DD."}), 400

    ajuste_pct = numero(data.get("ajuste_pct", 0), "ajuste_pct", minimo=-100, maximo=1000)
    factor = 1 + ajuste_pct / 100

    nueva = Tarifa(nombre=nombre, vigente_desde=vigente_desde, creada_por_id=usuario_actual().id)
    db.session.add(nueva)
    db.session.flush()  # para tener nueva.id antes de crear los precios

    for p in origen.precios:
        db.session.add(PrecioTarifa(
            tarifa_id=nueva.id,
            tipo_trabajo_id=p.tipo_trabajo_id,
            concepto=p.concepto,
            clave=p.clave,
            unidad=p.unidad,
            precio=round(float(p.precio) * factor, 2),
        ))

    db.session.commit()
    return jsonify(nueva.to_dict(con_precios=True)), 201
