import math
import os
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import quote
from flask import Blueprint, jsonify, request, current_app, send_file
from werkzeug.utils import secure_filename
from extensions import db
from models import Producto, Cotizacion, Partida, Proyecto, Tarifa, Usuario, Pago, FotoAvance, Bitacora, ESTADOS_PROYECTO, registrar_bitacora
from auth import requiere_rol, usuario_actual, generar_token_cotizacion
from validacion import numero
from dominio.despiece import despiece
from dominio.precios import cotizar_partida
from routes.cotizador import VIGENCIA_DIAS, TASA_IVA
from reportes import costo_real_por_proyecto, tasa_conversion_por_tipo, tasa_conversion_por_rango_precio, horas_por_m2

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
        precio_referencia_m2=numero(precio, "precio_referencia_m2", minimo=0.01),
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
        producto.precio_referencia_m2 = numero(request.form["precio_referencia_m2"], "precio_referencia_m2", minimo=0.01)
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
    return jsonify([_cotizacion_con_enlaces(c) for c in cotizaciones])


def _cotizacion_con_enlaces(cotizacion):
    """Agrega el link público de aceptación y uno de WhatsApp prellenado —
    un <a href>, no una integración (Fase 7.1/7.4)."""
    datos = cotizacion.to_dict()
    datos["token_publico"] = generar_token_cotizacion(cotizacion.id)
    total = cotizacion.total if cotizacion.total is not None else cotizacion.precio_estimado
    mensaje = f"Hola {cotizacion.nombre_cliente}, tu cotización {cotizacion.folio or ''} de Los Mejía por ${float(total):,.2f} está lista."
    telefono_limpio = "".join(ch for ch in (cotizacion.telefono or "") if ch.isdigit())
    if telefono_limpio:
        datos["link_whatsapp"] = f"https://wa.me/52{telefono_limpio}?text={quote(mensaje)}"
    return datos


@admin_bp.get("/cotizaciones/seguimiento")
@requiere_rol("administrador")
def seguimiento_cotizaciones():
    """La mayoría de las cotizaciones no se pierden por precio, se pierden
    por falta de seguimiento (Fase 7.4) — agrupa las que no han sido
    aceptadas ni rechazadas por cuántos días llevan sin respuesta."""
    hoy = datetime.utcnow()
    pendientes = Cotizacion.query.filter(
        Cotizacion.aceptada_en.is_(None),
        Cotizacion.estado.notin_(("rechazada", "vencida")),
    ).all()

    buckets = {"3_dias": [], "7_dias": [], "15_dias_o_mas": []}
    for c in pendientes:
        dias = (hoy - c.creado_en).days
        if dias >= 15:
            buckets["15_dias_o_mas"].append(_cotizacion_con_enlaces(c))
        elif dias >= 7:
            buckets["7_dias"].append(_cotizacion_con_enlaces(c))
        elif dias >= 3:
            buckets["3_dias"].append(_cotizacion_con_enlaces(c))
    return jsonify(buckets)


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/revivir")
@requiere_rol("administrador")
def revivir_cotizacion(cotizacion_id):
    """Revive una cotización vencida recalculando con la tarifa activa —
    una cotización de hace 4 meses con precios de hace 4 meses es una
    pérdida garantizada (Fase 7.4)."""
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    tarifa_activa = Tarifa.query.filter_by(activa=True).first()

    if cotizacion.partidas and tarifa_activa:
        subtotal = 0.0
        for partida in cotizacion.partidas:
            importe, desglose = cotizar_partida(partida.spec, partida.tipo_trabajo, tarifa_activa)
            partida.precio_unitario = desglose["importe_unitario"]
            partida.importe = importe
            partida.desglose = desglose
            subtotal += importe
        base = round(subtotal - float(cotizacion.descuento or 0), 2)
        iva = round(base * TASA_IVA, 2) if float(cotizacion.iva or 0) > 0 else 0.0
        cotizacion.subtotal = round(subtotal, 2)
        cotizacion.iva = iva
        cotizacion.total = round(base + iva, 2)
        cotizacion.tarifa_id = tarifa_activa.id

    cotizacion.vigencia_hasta = date.today() + timedelta(days=VIGENCIA_DIAS)
    cotizacion.estado = "nueva"
    cotizacion.aceptada_en = None
    cotizacion.aceptada_ip = None
    db.session.commit()
    return jsonify(cotizacion.to_dict())


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/aprobar")
@requiere_rol("administrador")
def aprobar_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    if cotizacion.proyecto:
        return jsonify({"error": "Esta cotización ya tiene un proyecto asociado."}), 400

    data = request.get_json(silent=True) or {}
    trabajador_id = data.get("trabajador_id")

    titulo = cotizacion.producto.nombre if cotizacion.producto else f"Proyecto {cotizacion.material} a medida"
    carga_proyecto = sum(float(p.cantidad) for p in cotizacion.partidas) or float(cotizacion.metros_cuadrados or 0)
    proyecto = Proyecto(
        cotizacion_id=cotizacion.id,
        cliente_id=cotizacion.cliente_id,
        trabajador_id=trabajador_id,
        titulo=titulo,
        # Fase 7.5: fecha estimada de entrega calculada a partir de la
        # carga real, no del optimismo.
        fecha_estimada_entrega=_calcular_fecha_entrega(carga_proyecto),
    )
    cotizacion.estado = "aprobada"
    db.session.add(proyecto)
    db.session.commit()
    return jsonify(proyecto.to_dict()), 201


# ---------- Agenda y capacidad (Fase 7.5) ----------

# Unidades de carga por semana (m² o ml, según la partida) que el taller
# puede procesar — ajustable; hoy es una constante porque no existe una
# pantalla de configuración de capacidad.
CAPACIDAD_SEMANAL = 40


def _carga_activa_total():
    proyectos_activos = Proyecto.query.filter(Proyecto.estado.in_(("pendiente", "en_proceso"))).all()
    return sum(float(p.cantidad) for proyecto in proyectos_activos for p in proyecto.cotizacion.partidas)


def _calcular_fecha_entrega(carga_nueva):
    semanas = math.ceil(max(1.0, (_carga_activa_total() + carga_nueva)) / CAPACIDAD_SEMANAL)
    return date.today() + timedelta(weeks=max(1, semanas))


@admin_bp.get("/agenda")
@requiere_rol("administrador")
def agenda_capacidad():
    """Avisa cuándo la semana ya está comprometida — prometer entregas que
    no se pueden cumplir es la forma más rápida de perder reputación en un
    negocio que vive de recomendaciones."""
    proyectos_activos = Proyecto.query.filter(Proyecto.estado.in_(("pendiente", "en_proceso"))).all()
    semanas = {}
    for proyecto in proyectos_activos:
        if not proyecto.fecha_estimada_entrega:
            continue
        inicio_semana = proyecto.fecha_estimada_entrega - timedelta(days=proyecto.fecha_estimada_entrega.weekday())
        clave = inicio_semana.isoformat()
        carga = sum(float(p.cantidad) for p in proyecto.cotizacion.partidas)
        semana = semanas.setdefault(clave, {"carga": 0.0, "proyectos": []})
        semana["carga"] += carga
        semana["proyectos"].append({"id": proyecto.id, "titulo": proyecto.titulo})

    return jsonify([
        {
            "semana_inicio": inicio,
            "carga": round(datos["carga"], 2),
            "capacidad": CAPACIDAD_SEMANAL,
            "sobrecargada": datos["carga"] > CAPACIDAD_SEMANAL,
            "proyectos": datos["proyectos"],
        }
        for inicio, datos in sorted(semanas.items())
    ])


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/rechazar")
@requiere_rol("administrador")
def rechazar_cotizacion(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    cotizacion.estado = "rechazada"
    db.session.commit()
    return jsonify(cotizacion.to_dict())


@admin_bp.post("/cotizaciones/<int:cotizacion_id>/simular")
@requiere_rol("administrador")
def simular_cotizacion(cotizacion_id):
    """Recalcula el precio con parámetros que el dueño ajusta en vivo — NO
    se guarda nada aquí, hasta que confirme desde otra pantalla (Fase 4.4).
    El material_base sale de las partidas ya cotizadas con la tarifa
    activa; mano de obra, flete, merma y utilidad son ajustables porque
    varían por trabajo y hoy no viven en ninguna tabla.

    Muestra el margen sobre venta, no el porcentaje de utilidad sobre
    costo — son números distintos: 25% sobre costo es ~20% sobre venta, y
    confundirlos hace creer que se gana más de lo que realmente se gana."""
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    data = request.get_json(force=True)

    material_base = sum(float(p.importe) for p in cotizacion.partidas) or float(cotizacion.precio_estimado or 0)
    mano_obra = numero(data.get("mano_obra", 0), "mano_obra", minimo=0)
    flete_km = numero(data.get("flete_km", 0), "flete_km", minimo=0)
    flete_precio_km = numero(data.get("flete_precio_km", 0), "flete_precio_km", minimo=0)
    merma_pct = numero(data.get("merma_pct", 0), "merma_pct", minimo=0, maximo=100)
    utilidad_pct = numero(data.get("utilidad_pct", 25), "utilidad_pct", minimo=0, maximo=500)
    descuento = numero(data.get("descuento", 0), "descuento", minimo=0)
    aplica_iva = bool(data.get("aplica_iva", False))

    merma = round(material_base * merma_pct / 100, 2)
    flete = round(flete_km * flete_precio_km, 2)
    costo_directo = round(material_base + merma + mano_obra + flete, 2)
    utilidad = round(costo_directo * utilidad_pct / 100, 2)
    subtotal = round(max(costo_directo + utilidad - descuento, 0), 2)
    iva = round(subtotal * 0.16, 2) if aplica_iva else 0.0
    total = round(subtotal + iva, 2)
    margen_sobre_venta_pct = round(utilidad / subtotal * 100, 2) if subtotal else 0.0

    return jsonify({
        "material_base": round(material_base, 2),
        "merma_pct": merma_pct, "merma": merma,
        "mano_obra": mano_obra, "flete": flete,
        "costo_directo": costo_directo,
        "utilidad_pct": utilidad_pct, "utilidad": utilidad,
        "margen_sobre_venta_pct": margen_sobre_venta_pct,
        "descuento": descuento, "subtotal": subtotal, "iva": iva, "total": total,
        "estimado_cliente_min": round(total * 0.9, 2),
        "estimado_cliente_max": round(total * 1.1, 2),
    })


# ---------- Despiece (lista de corte, Fase 5.1) ----------

@admin_bp.post("/partidas/<int:partida_id>/despiece")
@requiere_rol("administrador", "trabajador")
def despiece_de_partida(partida_id):
    """De la especificación ya guardada de una partida, saca cuántos tramos
    de perfil hacen falta y cómo acomodarlos en barras de 6 m. Aplica solo
    a piezas rectangulares con barrotes (portones, rejas, protecciones) —
    no a escalera ni a cancelería/vidrio."""
    partida = Partida.query.get_or_404(partida_id)
    data = request.get_json(silent=True) or {}
    merma_pct_teorica = numero(data.get("merma_pct_teorica", 7), "merma_pct_teorica", minimo=0, maximo=100)
    admite_barrotes = partida.tipo_trabajo.admite_barrotes if partida.tipo_trabajo else True
    return jsonify(despiece(partida.spec, merma_pct_teorica=merma_pct_teorica, admite_barrotes=admite_barrotes))


@admin_bp.get("/partidas/<int:partida_id>/orden-trabajo.pdf")
@requiere_rol("administrador", "trabajador")
def orden_trabajo_partida(partida_id):
    """PDF de taller: lista de corte y herrajes, sin precios."""
    partida = Partida.query.get_or_404(partida_id)
    merma_pct_teorica = numero(request.args.get("merma_pct_teorica", 7), "merma_pct_teorica", minimo=0, maximo=100)
    admite_barrotes = partida.tipo_trabajo.admite_barrotes if partida.tipo_trabajo else True
    resultado = despiece(partida.spec, merma_pct_teorica=merma_pct_teorica, admite_barrotes=admite_barrotes)

    from orden_trabajo_pdf import generar_orden_trabajo_pdf
    buffer = generar_orden_trabajo_pdf(partida.cotizacion, partida, resultado)
    nombre_archivo = f"orden-trabajo-{partida.cotizacion.folio or partida.cotizacion_id}-{partida.id}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=nombre_archivo)


@admin_bp.get("/requisicion")
@requiere_rol("administrador")
def requisicion_material():
    """Suma el material de todos los proyectos activos (Fase 5.2): cuántas
    barras comerciales de 6 m hacen falta en total, para comprar una vez en
    vez de ir al proveedor cada vez que se corta un trabajo. No distingue
    calibre ni perfil todavía — el spec de hoy no captura esos datos (ver
    dominio/spec.py) — así que es un total agregado, no una lista por
    calibre."""
    proyectos_activos = Proyecto.query.filter(Proyecto.estado.in_(("pendiente", "en_proceso"))).all()
    total_barras = 0
    detalle = []
    for proyecto in proyectos_activos:
        for partida in proyecto.cotizacion.partidas:
            admite_barrotes = partida.tipo_trabajo.admite_barrotes if partida.tipo_trabajo else True
            try:
                resultado = despiece(partida.spec, admite_barrotes=admite_barrotes)
            except (ValueError, KeyError, TypeError):
                continue  # pieza sin medidas de barrotes calculables (p. ej. cristal templado sin marco)
            total_barras += resultado["num_barras"]
            detalle.append({
                "proyecto_id": proyecto.id,
                "proyecto_titulo": proyecto.titulo,
                "partida_id": partida.id,
                "descripcion": partida.descripcion,
                "num_barras": resultado["num_barras"],
            })
    return jsonify({"total_barras_6m": total_barras, "detalle": detalle})


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
    usuario = usuario_actual()

    if "trabajador_id" in data and data["trabajador_id"] != proyecto.trabajador_id:
        registrar_bitacora(usuario.id, "proyecto", proyecto.id, "asignacion",
                            antes={"trabajador_id": proyecto.trabajador_id}, despues={"trabajador_id": data["trabajador_id"]})
        proyecto.trabajador_id = data["trabajador_id"]

    if "estado" in data and data["estado"] in ESTADOS_PROYECTO and data["estado"] != proyecto.estado:
        # Regla de negocio (Fase 7.2): ningún proyecto pasa a "en_proceso"
        # sin anticipo registrado — evita comprar material para un trabajo
        # que se cayó, el problema más caro de un taller chico.
        if data["estado"] == "en_proceso" and not proyecto.pagos:
            return jsonify({"error": "Este proyecto no tiene ningún pago registrado. Registra el anticipo antes de pasarlo a 'en_proceso'."}), 400
        registrar_bitacora(usuario.id, "proyecto", proyecto.id, "cambio_estado",
                            antes={"estado": proyecto.estado}, despues={"estado": data["estado"]})
        proyecto.estado = data["estado"]

    if "avance_porcentaje" in data:
        proyecto.avance_porcentaje = max(0, min(100, int(numero(data["avance_porcentaje"], "avance_porcentaje", minimo=0, maximo=100))))
    if "notas_internas" in data:
        proyecto.notas_internas = data["notas_internas"]
    if "costo_material_real" in data:
        # Fase 8.1: costo real, capturado a mano al conciliar el proyecto —
        # no hay ninguna integración de compras que lo llene solo.
        proyecto.costo_material_real = numero(data["costo_material_real"], "costo_material_real", minimo=0)

    db.session.commit()
    return jsonify(proyecto.to_dict())


@admin_bp.post("/proyectos/<int:proyecto_id>/pagos")
@requiere_rol("administrador")
def registrar_pago(proyecto_id):
    """Anticipos y estado de cuenta (Fase 7.2): las herrerías viven del
    anticipo, 50% para comprar material y 50% contra entrega."""
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    data = request.get_json(force=True)
    monto = numero(data.get("monto"), "monto", minimo=0.01)
    fecha_str = data.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else date.today()
    except ValueError:
        return jsonify({"error": "'fecha' debe tener formato AAAA-MM-DD."}), 400

    pago = Pago(
        proyecto_id=proyecto.id,
        monto=monto,
        metodo=data.get("metodo"),
        fecha=fecha,
        comprobante_url=data.get("comprobante_url"),
        registrado_por_id=usuario_actual().id,
    )
    db.session.add(pago)
    db.session.commit()
    return jsonify(proyecto.to_dict()), 201


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


@admin_bp.put("/usuarios/<int:usuario_id>/password")
@requiere_rol("administrador")
def restablecer_password(usuario_id):
    """No hay recuperación de contraseña por correo (decisión deliberada,
    ver README): el administrador la restablece desde aquí. Invalida
    también cualquier sesión que esa persona tuviera abierta."""
    usuario = Usuario.query.get_or_404(usuario_id)
    data = request.get_json(force=True)
    password_nueva = data.get("password_nueva", "")

    if len(password_nueva) < 6:
        return jsonify({"error": "La contraseña nueva debe tener al menos 6 caracteres."}), 400

    usuario.set_password(password_nueva)
    usuario.token_version += 1
    db.session.commit()
    return jsonify({"ok": True})


# ---------- Bitácora de auditoría (Fase 7.6) ----------

@admin_bp.get("/bitacora")
@requiere_rol("administrador")
def listar_bitacora():
    """Con tres roles y varias personas tocando los mismos registros,
    '¿quién le bajó el precio a esta cotización?' es una pregunta que se va
    a hacer — conviene que tenga respuesta."""
    query = Bitacora.query
    entidad = request.args.get("entidad")
    if entidad:
        query = query.filter_by(entidad=entidad)
    entidad_id = request.args.get("entidad_id")
    if entidad_id:
        query = query.filter_by(entidad_id=int(numero(entidad_id, "entidad_id", minimo=1)))
    registros = query.order_by(Bitacora.creado_en.desc()).limit(200).all()
    return jsonify([r.to_dict() for r in registros])


# ---------- Los números del negocio (Fase 8) ----------

@admin_bp.get("/reportes/costo-real")
@requiere_rol("administrador")
def reporte_costo_real():
    """El único reporte que realmente importa: revela qué tipo de pieza
    deja dinero y cuál se cotiza por debajo del costo."""
    return jsonify(costo_real_por_proyecto())


@admin_bp.get("/reportes/conversion")
@requiere_rol("administrador")
def reporte_conversion():
    return jsonify({
        "por_tipo": tasa_conversion_por_tipo(),
        "por_rango_precio": tasa_conversion_por_rango_precio(),
    })


@admin_bp.get("/reportes/horas-por-m2")
@requiere_rol("administrador")
def reporte_horas_por_m2():
    return jsonify(horas_por_m2())


@admin_bp.get("/reportes/excel")
@requiere_rol("administrador")
def reporte_excel():
    from reportes_excel import generar_reportes_excel
    buffer = generar_reportes_excel(
        costo_real_por_proyecto(), tasa_conversion_por_tipo(),
        tasa_conversion_por_rango_precio(), horas_por_m2(),
    )
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="reportes-los-mejia.xlsx",
    )
