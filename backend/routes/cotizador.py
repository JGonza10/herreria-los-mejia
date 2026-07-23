from flask import Blueprint, jsonify, request
from extensions import db
from models import PrecioMaterial, Cotizacion, Producto
from auth import usuario_actual

cotizador_bp = Blueprint("cotizador", __name__)


def calcular_precio(material: str, ancho_m: float, alto_m: float, con_acabado: bool):
    precio = PrecioMaterial.query.filter_by(material=material).first()
    if precio is None:
        raise ValueError(f"No hay precio configurado para el material '{material}'")

    m2 = round(ancho_m * alto_m, 2)
    precio_m2 = float(precio.precio_base_m2)
    if con_acabado:
        precio_m2 += float(precio.precio_acabado_extra_m2)

    total = round(m2 * precio_m2, 2)
    return m2, total


@cotizador_bp.get("/precios")
def precios_por_material():
    precios = PrecioMaterial.query.all()
    return jsonify([p.to_dict() for p in precios])


@cotizador_bp.post("/calcular")
def calcular():
    data = request.get_json(force=True)
    try:
        material = data["material"]
        ancho_m = float(data["ancho_m"])
        alto_m = float(data["alto_m"])
        con_acabado = bool(data.get("con_acabado", False))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Datos inválidos. Se requiere material, ancho_m y alto_m."}), 400

    try:
        m2, total = calcular_precio(material, ancho_m, alto_m, con_acabado)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"metros_cuadrados": m2, "precio_estimado": total})


@cotizador_bp.post("/solicitar")
def solicitar_cotizacion():
    """Crea una cotización. Puede venir de un visitante (sin sesión) o de un
    cliente logueado — en ese caso se liga a su cuenta automáticamente.
    Si trae producto_id, es una cotización basada en un modelo del catálogo;
    si no, es una propuesta personalizada (material + medidas libres)."""
    data = request.get_json(force=True)
    required = ["nombre_cliente", "telefono", "material", "ancho_m", "alto_m"]
    faltantes = [campo for campo in required if campo not in data]
    if faltantes:
        return jsonify({"error": f"Faltan campos: {', '.join(faltantes)}"}), 400

    producto_id = data.get("producto_id")
    if producto_id and not Producto.query.get(producto_id):
        return jsonify({"error": "El producto seleccionado no existe."}), 400

    try:
        ancho_m = float(data["ancho_m"])
        alto_m = float(data["alto_m"])
        con_acabado = bool(data.get("con_acabado", False))
        m2, total = calcular_precio(data["material"], ancho_m, alto_m, con_acabado)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    usuario = usuario_actual()

    cotizacion = Cotizacion(
        cliente_id=usuario.id if usuario else None,
        producto_id=producto_id,
        nombre_cliente=data["nombre_cliente"],
        telefono=data["telefono"],
        email=data.get("email"),
        material=data["material"],
        ancho_m=ancho_m,
        alto_m=alto_m,
        con_acabado=con_acabado,
        metros_cuadrados=m2,
        precio_estimado=total,
        notas=data.get("notas"),
    )
    db.session.add(cotizacion)
    db.session.commit()

    return jsonify(cotizacion.to_dict()), 201
