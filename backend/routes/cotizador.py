from flask import Blueprint, jsonify, request
from extensions import db
from models import PrecioMaterial, Cotizacion, Producto, TipoTrabajo
from auth import usuario_actual
from validacion import numero
from dominio.precios import calcular_precio
from dominio.spec import construir_basico

cotizador_bp = Blueprint("cotizador", __name__)

ANCHO_MAXIMO_M = 15
ALTO_MAXIMO_M = 6


@cotizador_bp.get("/precios")
def precios_por_material():
    precios = PrecioMaterial.query.all()
    return jsonify([p.to_dict() for p in precios])


@cotizador_bp.get("/tipos-trabajo")
def tipos_trabajo():
    """Catálogo de qué se puede fabricar (ver dominio/spec.py) — en tabla,
    no en el frontend, para que el dueño pueda agregar tipos sin redesplegar."""
    tipos = TipoTrabajo.query.filter_by(activo=True).order_by(TipoTrabajo.nombre.asc()).all()
    return jsonify([t.to_dict() for t in tipos])


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

    # "indefinido" porque el catálogo todavía no liga cada producto a un
    # TipoTrabajo (ver Fase 4) — es el fallback que el propio plan describe,
    # no un dato inventado.
    spec = construir_basico(data["material"], ancho_m, alto_m, con_acabado, tipo="indefinido")

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
        spec=spec,
    )
    db.session.add(cotizacion)
    db.session.commit()

    return jsonify(cotizacion.to_dict()), 201
