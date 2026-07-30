from datetime import date, datetime, timedelta
from flask import Blueprint, jsonify, request
from extensions import db
from models import PrecioMaterial, Cotizacion, Partida, Producto, Tarifa, TipoTrabajo
from auth import usuario_actual, generar_token_cotizacion, leer_token_cotizacion
from validacion import numero
from dominio.precios import calcular_precio, cotizar_partida
from dominio.spec import construir_basico

cotizador_bp = Blueprint("cotizador", __name__)

ANCHO_MAXIMO_M = 15
ALTO_MAXIMO_M = 6
VIGENCIA_DIAS = 30
TASA_IVA = 0.16


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
    si no, es una propuesta personalizada (material + medidas libres).

    Si el cuerpo trae 'piezas' (lista), es una cotización con varias
    partidas (Fase 4.1/4.3): cada pieza se cotiza con la tarifa activa y su
    propia estrategia de cobro por sistema. Sin 'piezas', se comporta
    exactamente igual que siempre — el frontend actual (Cotizador.jsx)
    manda una sola pieza y sigue funcionando sin cambios."""
    data = request.get_json(force=True)
    if data.get("piezas"):
        return _solicitar_multiple(data)

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

    return jsonify({**cotizacion.to_dict(), "token_publico": generar_token_cotizacion(cotizacion.id)}), 201


def _solicitar_multiple(data):
    required = ["nombre_cliente", "telefono"]
    faltantes = [campo for campo in required if campo not in data]
    if faltantes:
        return jsonify({"error": f"Faltan campos: {', '.join(faltantes)}"}), 400

    piezas_data = data["piezas"]
    if not isinstance(piezas_data, list) or not piezas_data:
        return jsonify({"error": "'piezas' debe ser una lista con al menos un elemento."}), 400

    tarifa = Tarifa.query.filter_by(activa=True).first()
    if not tarifa:
        return jsonify({"error": "No hay una tarifa activa. Actívala en Admin → Tarifas antes de cotizar."}), 400

    usuario = usuario_actual()
    cotizacion = Cotizacion(
        cliente_id=usuario.id if usuario else None,
        nombre_cliente=data["nombre_cliente"],
        telefono=data["telefono"],
        email=data.get("email"),
        notas=data.get("notas"),
        tarifa_id=tarifa.id,
        vigencia_hasta=date.today() + timedelta(days=VIGENCIA_DIAS),
        # Los campos heredados (material/ancho_m/...) reflejan la primera
        # partida, para que un consumidor que todavía espera una sola pieza
        # (el frontend actual no llama esta ruta, pero el modelo lo permite)
        # no se rompa con nulos.
        material="", ancho_m=0, alto_m=0, metros_cuadrados=0, precio_estimado=0,
    )

    subtotal = 0
    for i, pieza in enumerate(piezas_data):
        prefijo = f"piezas[{i}]"
        material = (pieza.get("material") or "").strip()
        if not material:
            return jsonify({"error": f"{prefijo}.material es obligatorio."}), 400

        tipo_clave = pieza.get("tipo") or "indefinido"
        tipo_trabajo = TipoTrabajo.query.filter_by(clave=tipo_clave, activo=True).first()

        ancho_m = numero(pieza.get("ancho_m"), f"{prefijo}.ancho_m", minimo=0.1, maximo=ANCHO_MAXIMO_M)
        alto_m = numero(pieza.get("alto_m"), f"{prefijo}.alto_m", minimo=0.1, maximo=ALTO_MAXIMO_M)
        con_acabado = bool(pieza.get("con_acabado", False))
        n_piezas = int(numero(pieza.get("piezas", 1), f"{prefijo}.piezas", minimo=1, maximo=200))

        spec = construir_basico(material, ancho_m, alto_m, con_acabado, tipo=tipo_clave,
                                 sistema=tipo_trabajo.sistema if tipo_trabajo else None)
        spec["material"] = material
        spec["piezas"] = n_piezas

        importe, desglose = cotizar_partida(spec, tipo_trabajo, tarifa)
        cantidad = desglose.get("longitud_ml", desglose.get("area_m2", 0))
        precio_unitario = desglose["importe_unitario"]

        partida = Partida(
            tipo_trabajo_id=tipo_trabajo.id if tipo_trabajo else None,
            spec=spec,
            descripcion=pieza.get("descripcion") or (tipo_trabajo.nombre if tipo_trabajo else tipo_clave),
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            desglose=desglose,
            orden=i,
        )
        cotizacion.partidas.append(partida)
        subtotal += importe

        if i == 0:
            cotizacion.material = material
            cotizacion.ancho_m = ancho_m
            cotizacion.alto_m = alto_m
            cotizacion.con_acabado = con_acabado
            cotizacion.metros_cuadrados = cantidad
            cotizacion.precio_estimado = importe
            cotizacion.spec = spec

    descuento = numero(data.get("descuento", 0), "descuento", minimo=0, maximo=subtotal)
    aplica_iva = bool(data.get("aplica_iva", False))
    base = round(subtotal - descuento, 2)
    iva = round(base * TASA_IVA, 2) if aplica_iva else 0
    total = round(base + iva, 2)

    cotizacion.subtotal = round(subtotal, 2)
    cotizacion.descuento = descuento
    cotizacion.iva = iva
    cotizacion.total = total

    db.session.add(cotizacion)
    db.session.flush()  # asigna cotizacion.id, usado en el folio
    cotizacion.folio = f"LM-{date.today().year}-{cotizacion.id:04d}"
    db.session.commit()

    return jsonify({**cotizacion.to_dict(), "token_publico": generar_token_cotizacion(cotizacion.id)}), 201


@cotizador_bp.get("/publica/<token>")
def ver_cotizacion_publica(token):
    """Link público de la Fase 7.1 — el cliente ve su ficha con el dibujo
    (cuando exista) y un botón de 'Acepto esta cotización'. El token en sí
    no expira; la vigencia real la marca vigencia_hasta."""
    cotizacion_id = leer_token_cotizacion(token)
    if not cotizacion_id:
        return jsonify({"error": "Enlace inválido."}), 404
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    datos = cotizacion.to_dict()
    datos["vencida"] = bool(cotizacion.vigencia_hasta and cotizacion.vigencia_hasta < date.today())
    return jsonify(datos)


@cotizador_bp.post("/publica/<token>/aceptar")
def aceptar_cotizacion_publica(token):
    """Guarda fecha, hora e IP de la aceptación — no es un contrato ante
    notario, pero es infinitamente mejor que 'usted me dijo que sí por
    teléfono'."""
    cotizacion_id = leer_token_cotizacion(token)
    if not cotizacion_id:
        return jsonify({"error": "Enlace inválido."}), 404
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)

    if cotizacion.vigencia_hasta and cotizacion.vigencia_hasta < date.today():
        return jsonify({"error": "Esta cotización ya venció. Pide que te la revivan con los precios actuales."}), 400
    if cotizacion.aceptada_en:
        return jsonify({"error": "Esta cotización ya había sido aceptada."}), 400

    cotizacion.aceptada_en = datetime.utcnow()
    cotizacion.aceptada_ip = request.remote_addr
    db.session.commit()
    return jsonify(cotizacion.to_dict())
