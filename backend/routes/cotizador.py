from flask import Blueprint, jsonify, request
from extensions import db
from models import PrecioMaterial, Cotizacion, Producto
from auth import usuario_actual
from validacion import numero

cotizador_bp = Blueprint("cotizador", __name__)

ANCHO_MAXIMO_M = 15
ALTO_MAXIMO_M = 6


def calcular_precio(material: str, ancho_m: float, alto_m: float, con_acabado: bool, producto: Producto = None):
    """Si se pasa `producto` (modelo elegido del catálogo), se usa su propio
    precio_referencia_m2 como base — cada modelo puede costar distinto aunque
    sea del mismo material. Si no, se usa el precio genérico por material
    (propuesta personalizada, sin modelo específico). El extra por acabado
    especial siempre sale de la tabla genérica por material."""
    precio_material = PrecioMaterial.query.filter_by(material=material).first()
    if precio_material is None:
        raise ValueError(f"No hay precio configurado para el material '{material}'")

    m2 = round(ancho_m * alto_m, 2)
    precio_m2 = float(producto.precio_referencia_m2) if producto else float(precio_material.precio_base_m2)
    if con_acabado:
        precio_m2 += float(precio_material.precio_acabado_extra_m2)

    total = round(m2 * precio_m2, 2)
    return m2, total


@cotizador_bp.get("/precios")
def precios_por_material():
    precios = PrecioMaterial.query.all()
    return jsonify([p.to_dict() for p in precios])


@cotizador_bp.post("/calcular")
def calcular():
    data = request.get_json(force=True)
    material = data.get("material")
    if not material:
        return jsonify({"error": "Falta 'material'."}), 400

    ancho_m = numero(data.get("ancho_m"), "ancho_m", minimo=0.1, maximo=ANCHO_MAXIMO_M)
    alto_m = numero(data.get("alto_m"), "alto_m", minimo=0.1, maximo=ALTO_MAXIMO_M)
    con_acabado = bool(data.get("con_acabado", False))

    producto = None
    producto_id = data.get("producto_id")
    if producto_id:
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({"error": "El producto seleccionado no existe."}), 400

    m2, total = calcular_precio(material, ancho_m, alto_m, con_acabado, producto)
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
    producto = Producto.query.get(producto_id) if producto_id else None
    if producto_id and not producto:
        return jsonify({"error": "El producto seleccionado no existe."}), 400

    ancho_m = numero(data["ancho_m"], "ancho_m", minimo=0.1, maximo=ANCHO_MAXIMO_M)
    alto_m = numero(data["alto_m"], "alto_m", minimo=0.1, maximo=ALTO_MAXIMO_M)
    con_acabado = bool(data.get("con_acabado", False))
    m2, total = calcular_precio(data["material"], ancho_m, alto_m, con_acabado, producto)

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
