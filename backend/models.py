from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

ROLES = ("administrador", "trabajador", "cliente")
ESTADOS_COTIZACION = ("nueva", "revisada", "aprobada", "rechazada", "vencida")
ESTADOS_PROYECTO = ("pendiente", "en_proceso", "terminado", "entregado", "cancelado")
SISTEMAS = ("herreria", "aluminio", "cristal_templado")
UNIDADES_TIPO_TRABAJO = ("m2", "ml")


class TipoTrabajo(db.Model):
    """Catálogo de qué se puede fabricar, en tabla (no enum en código) para
    que el dueño pueda agregar tipos sin tocar código ni redesplegar."""
    __tablename__ = "tipos_trabajo"

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(40), unique=True, nullable=False)
    nombre = db.Column(db.String(80), nullable=False)
    sistema = db.Column(db.String(20), nullable=False)
    unidad = db.Column(db.String(4), nullable=False)
    altura_referencia_m = db.Column(db.Numeric(4, 2), nullable=True)
    modo_dibujo = db.Column(db.String(20), nullable=False)
    admite_barrotes = db.Column(db.Boolean, default=True)
    minimo_facturable = db.Column(db.Numeric(5, 2), default=1)
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "clave": self.clave,
            "nombre": self.nombre,
            "sistema": self.sistema,
            "unidad": self.unidad,
            "altura_referencia_m": float(self.altura_referencia_m) if self.altura_referencia_m is not None else None,
            "modo_dibujo": self.modo_dibujo,
            "admite_barrotes": self.admite_barrotes,
            "minimo_facturable": float(self.minimo_facturable),
            "activo": self.activo,
        }


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="cliente")
    activo = db.Column(db.Boolean, default=True)
    # Incluida en cada token de sesión y verificada al validarlo (ver auth.py).
    # Subirla invalida de golpe todas las sesiones activas de este usuario —
    # los tokens son sin estado y viven 30 días, así que es la única forma
    # barata de revocarlos si a alguien le roban uno.
    token_version = db.Column(db.Integer, nullable=False, default=0)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol,
            "activo": self.activo,
        }


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    material = db.Column(db.String(20), nullable=False)  # hierro | aluminio | vidrio
    descripcion = db.Column(db.Text, nullable=True)
    precio_referencia_m2 = db.Column(db.Numeric(10, 2), nullable=False)
    imagen_url = db.Column(db.String(300), nullable=True)
    destacado = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "material": self.material,
            "descripcion": self.descripcion,
            "precio_referencia_m2": float(self.precio_referencia_m2),
            "imagen_url": self.imagen_url,
            "destacado": self.destacado,
            "activo": self.activo,
        }


class PrecioMaterial(db.Model):
    """Precio base por m2 y por acabado, usado por el cotizador."""
    __tablename__ = "precios_material"

    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.String(20), unique=True, nullable=False)
    precio_base_m2 = db.Column(db.Numeric(10, 2), nullable=False)
    precio_acabado_extra_m2 = db.Column(db.Numeric(10, 2), default=0)

    def to_dict(self):
        return {
            "material": self.material,
            "precio_base_m2": float(self.precio_base_m2),
            "precio_acabado_extra_m2": float(self.precio_acabado_extra_m2),
        }


class Cotizacion(db.Model):
    __tablename__ = "cotizaciones"
    __table_args__ = (
        db.Index("ix_cotizaciones_estado_creado_en", "estado", "creado_en"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, index=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=True)

    nombre_cliente = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    material = db.Column(db.String(20), nullable=False)
    ancho_m = db.Column(db.Numeric(6, 2), nullable=False)
    alto_m = db.Column(db.Numeric(6, 2), nullable=False)
    con_acabado = db.Column(db.Boolean, default=False)
    metros_cuadrados = db.Column(db.Numeric(8, 2), nullable=False)
    precio_estimado = db.Column(db.Numeric(10, 2), nullable=False)
    notas = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), default="nueva")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Especificación unificada de la pieza (ver backend/dominio/spec.py) — de
    # aquí van a salir el dibujo 2D/3D, el desglose de precio y el despiece,
    # sin que cada uno tenga su propia idea de qué se está fabricando.
    # Nullable porque las cotizaciones creadas antes de esta columna no la
    # tienen — ver backend/migrar_specs.py para el backfill.
    spec = db.Column(db.JSON, nullable=True)

    # Fase 4.1: una cotización puede tener varias partidas (piezas). Los
    # campos de arriba (material/ancho_m/alto_m/precio_estimado) se
    # conservan para no romper al frontend actual, que todavía muestra una
    # cotización como una sola pieza — reflejan siempre la primera partida.
    # folio/vigencia/subtotal/descuento/iva/total y tarifa_id son nullable
    # porque las cotizaciones viejas no los tienen — ver migrar_partidas.py.
    folio = db.Column(db.String(20), unique=True, nullable=True)
    vigencia_hasta = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=True)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), nullable=True)
    tarifa_id = db.Column(db.Integer, db.ForeignKey("tarifas.id"), nullable=True)

    # Fase 7.1: aceptación por el cliente vía link público con token firmado
    # (ver auth.py, generar_token_cotizacion). No es un contrato ante
    # notario, pero es mejor que "usted me dijo que sí por teléfono".
    aceptada_en = db.Column(db.DateTime, nullable=True)
    aceptada_ip = db.Column(db.String(45), nullable=True)

    producto = db.relationship("Producto")
    proyecto = db.relationship("Proyecto", back_populates="cotizacion", uselist=False)
    partidas = db.relationship("Partida", back_populates="cotizacion", cascade="all, delete-orphan", order_by="Partida.orden")

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "producto_id": self.producto_id,
            "producto_nombre": self.producto.nombre if self.producto else None,
            "nombre_cliente": self.nombre_cliente,
            "telefono": self.telefono,
            "email": self.email,
            "material": self.material,
            "ancho_m": float(self.ancho_m),
            "alto_m": float(self.alto_m),
            "con_acabado": self.con_acabado,
            "metros_cuadrados": float(self.metros_cuadrados),
            "precio_estimado": float(self.precio_estimado),
            "notas": self.notas,
            "estado": self.estado,
            "spec": self.spec,
            "folio": self.folio,
            "vigencia_hasta": self.vigencia_hasta.isoformat() if self.vigencia_hasta else None,
            "subtotal": float(self.subtotal) if self.subtotal is not None else None,
            "descuento": float(self.descuento) if self.descuento is not None else 0.0,
            "iva": float(self.iva) if self.iva is not None else 0.0,
            "total": float(self.total) if self.total is not None else None,
            "tarifa_id": self.tarifa_id,
            "partidas": [p.to_dict() for p in self.partidas],
            "tiene_proyecto": self.proyecto is not None,
            "aceptada_en": self.aceptada_en.isoformat() if self.aceptada_en else None,
            "aceptada_ip": self.aceptada_ip,
            "creado_en": self.creado_en.isoformat(),
        }


class Partida(db.Model):
    """Una pieza dentro de una cotización. Hoy el cotizador solo crea una
    partida por cotización (ver routes/cotizador.py); el modelo ya admite
    varias para cuando el formulario deje capturar más de una pieza en la
    misma solicitud, sin volver a tocar el esquema."""
    __tablename__ = "partidas"

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), nullable=False, index=True)
    tipo_trabajo_id = db.Column(db.Integer, db.ForeignKey("tipos_trabajo.id"), nullable=True)
    spec = db.Column(db.JSON, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    cantidad = db.Column(db.Numeric(8, 2), nullable=False)       # m² o ml, según el tipo
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    importe = db.Column(db.Numeric(12, 2), nullable=False)
    desglose = db.Column(db.JSON, nullable=True)
    orden = db.Column(db.Integer, default=0)

    cotizacion = db.relationship("Cotizacion", back_populates="partidas")
    tipo_trabajo = db.relationship("TipoTrabajo")

    def to_dict(self):
        return {
            "id": self.id,
            "cotizacion_id": self.cotizacion_id,
            "tipo_trabajo_id": self.tipo_trabajo_id,
            "tipo_trabajo_nombre": self.tipo_trabajo.nombre if self.tipo_trabajo else None,
            "spec": self.spec,
            "descripcion": self.descripcion,
            "cantidad": float(self.cantidad),
            "precio_unitario": float(self.precio_unitario),
            "importe": float(self.importe),
            "desglose": self.desglose,
            "orden": self.orden,
        }


class Proyecto(db.Model):
    """Un pedido en curso, generado al aprobar una cotización."""
    __tablename__ = "proyectos"
    __table_args__ = (
        db.Index("ix_proyectos_trabajador_estado", "trabajador_id", "estado"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    titulo = db.Column(db.String(160), nullable=False)
    estado = db.Column(db.String(20), default="pendiente")
    avance_porcentaje = db.Column(db.Integer, default=0)
    notas_internas = db.Column(db.Text, nullable=True)
    fecha_estimada_entrega = db.Column(db.Date, nullable=True)
    # Fase 8.1: costo real de material, capturado a mano por el
    # administrador al conciliar el proyecto (comprar materia prima no está
    # automatizado en ningún lado) — nullable hasta que se concilie.
    costo_material_real = db.Column(db.Numeric(10, 2), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cotizacion = db.relationship("Cotizacion", back_populates="proyecto")
    cliente = db.relationship("Usuario", foreign_keys=[cliente_id])
    trabajador = db.relationship("Usuario", foreign_keys=[trabajador_id])
    pagos = db.relationship("Pago", back_populates="proyecto", cascade="all, delete-orphan", order_by="Pago.fecha")
    fotos = db.relationship("FotoAvance", back_populates="proyecto", cascade="all, delete-orphan", order_by="FotoAvance.creado_en")
    registros_horas = db.relationship("RegistroHoras", back_populates="proyecto", cascade="all, delete-orphan", order_by="RegistroHoras.fecha")

    @property
    def total_pagado(self):
        return sum((float(p.monto) for p in self.pagos), 0.0)

    @property
    def total_horas(self):
        return sum((float(r.horas) for r in self.registros_horas), 0.0)

    def to_dict(self):
        precio_total = float(self.cotizacion.total) if self.cotizacion.total is not None else float(self.cotizacion.precio_estimado)
        return {
            "id": self.id,
            "cotizacion_id": self.cotizacion_id,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre if self.cliente else self.cotizacion.nombre_cliente,
            "trabajador_id": self.trabajador_id,
            "trabajador_nombre": self.trabajador.nombre if self.trabajador else None,
            "titulo": self.titulo,
            "estado": self.estado,
            "avance_porcentaje": self.avance_porcentaje,
            "notas_internas": self.notas_internas,
            "fecha_estimada_entrega": self.fecha_estimada_entrega.isoformat() if self.fecha_estimada_entrega else None,
            "creado_en": self.creado_en.isoformat(),
            "actualizado_en": self.actualizado_en.isoformat(),
            "material": self.cotizacion.material,
            "precio_estimado": float(self.cotizacion.precio_estimado),
            "total_pagado": round(self.total_pagado, 2),
            "saldo": round(precio_total - self.total_pagado, 2),
            "pagos": [p.to_dict() for p in self.pagos],
            "fotos": [f.to_dict() for f in self.fotos],
            "costo_material_real": float(self.costo_material_real) if self.costo_material_real is not None else None,
            "total_horas": round(self.total_horas, 2),
            "registros_horas": [r.to_dict() for r in self.registros_horas],
        }


class Tarifa(db.Model):
    """Un conjunto completo de precios con fecha de vigencia. Nunca se
    edita: se crea una nueva versión. Solo puede haber una `activa` a la vez
    (ver routes/admin.py, activar_tarifa) — las cotizaciones futuras usan la
    activa; las viejas conservan la que usaron cuando se crearon."""
    __tablename__ = "tarifas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    vigente_desde = db.Column(db.Date, nullable=False)
    activa = db.Column(db.Boolean, default=False)
    creada_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)

    precios = db.relationship("PrecioTarifa", cascade="all, delete-orphan", backref="tarifa")

    def to_dict(self, con_precios=False):
        datos = {
            "id": self.id,
            "nombre": self.nombre,
            "vigente_desde": self.vigente_desde.isoformat(),
            "activa": self.activa,
            "creada_en": self.creada_en.isoformat(),
        }
        if con_precios:
            datos["precios"] = [p.to_dict() for p in self.precios]
        return datos


class PrecioTarifa(db.Model):
    __tablename__ = "precios_tarifa"
    __table_args__ = (
        db.Index("ix_precios_tarifa_tarifa_id", "tarifa_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tarifa_id = db.Column(db.Integer, db.ForeignKey("tarifas.id"), nullable=False)
    tipo_trabajo_id = db.Column(db.Integer, db.ForeignKey("tipos_trabajo.id"), nullable=True)
    concepto = db.Column(db.String(40), nullable=False)   # material_base, acabado, perfil, cristal, herraje, mano_obra...
    clave = db.Column(db.String(40), nullable=False)      # hierro, aluminio, ptr_1.5_cal14, templado_6mm...
    unidad = db.Column(db.String(6), nullable=False)      # m2, ml, pza, %
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tarifa_id": self.tarifa_id,
            "tipo_trabajo_id": self.tipo_trabajo_id,
            "concepto": self.concepto,
            "clave": self.clave,
            "unidad": self.unidad,
            "precio": float(self.precio),
        }


class Pago(db.Model):
    """Un anticipo o pago parcial de un proyecto (Fase 7.2). Las herrerías
    viven del anticipo: 50% para comprar material, 50% contra entrega — y
    hasta ahora no había dónde registrarlo."""
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyectos.id"), nullable=False, index=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(db.String(30), nullable=True)   # efectivo, transferencia...
    fecha = db.Column(db.Date, nullable=False)
    comprobante_url = db.Column(db.String(300), nullable=True)
    registrado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    proyecto = db.relationship("Proyecto", back_populates="pagos")

    def to_dict(self):
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "monto": float(self.monto),
            "metodo": self.metodo,
            "fecha": self.fecha.isoformat(),
            "comprobante_url": self.comprobante_url,
            "registrado_por_id": self.registrado_por_id,
            "creado_en": self.creado_en.isoformat(),
        }


class FotoAvance(db.Model):
    """Foto de avance de un proyecto, subida por el trabajador desde el
    teléfono (Fase 7.3) — reduce las llamadas de '¿cómo va mi portón?'."""
    __tablename__ = "fotos_avance"

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyectos.id"), nullable=False, index=True)
    url = db.Column(db.String(300), nullable=False)
    subida_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    notas = db.Column(db.String(200), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    proyecto = db.relationship("Proyecto", back_populates="fotos")

    def to_dict(self):
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "url": self.url,
            "subida_por_id": self.subida_por_id,
            "notas": self.notas,
            "creado_en": self.creado_en.isoformat(),
        }


class Bitacora(db.Model):
    """Auditoría de cambios sensibles (Fase 7.6): precios, estados,
    asignaciones. Con tres roles y varias personas tocando los mismos
    registros, '¿quién le bajó el precio a esta cotización?' es una
    pregunta que se va a hacer — conviene que tenga respuesta."""
    __tablename__ = "bitacora"
    __table_args__ = (
        db.Index("ix_bitacora_entidad", "entidad", "entidad_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    entidad = db.Column(db.String(40), nullable=False)   # "cotizacion", "proyecto", "tarifa"...
    entidad_id = db.Column(db.Integer, nullable=False)
    accion = db.Column(db.String(40), nullable=False)    # "cambio_precio", "cambio_estado", "asignacion"...
    antes = db.Column(db.JSON, nullable=True)
    despues = db.Column(db.JSON, nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario.nombre if self.usuario else None,
            "entidad": self.entidad,
            "entidad_id": self.entidad_id,
            "accion": self.accion,
            "antes": self.antes,
            "despues": self.despues,
            "creado_en": self.creado_en.isoformat(),
        }


def registrar_bitacora(usuario_id, entidad, entidad_id, accion, antes=None, despues=None):
    """Helper para no repetir el patrón en cada ruta que cambia algo
    sensible — no hace commit, se agrega a la misma transacción del
    caller."""
    db.session.add(Bitacora(
        usuario_id=usuario_id, entidad=entidad, entidad_id=entidad_id,
        accion=accion, antes=antes, despues=despues,
    ))


class RegistroHoras(db.Model):
    """Horas trabajadas por un trabajador en un proyecto (Fase 8.3) — para
    calibrar la mano de obra con datos en vez de con corazonada. Hoy
    '320 $/m²' es un número inventado; con dos meses de registro deja de
    serlo."""
    __tablename__ = "registro_horas"

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyectos.id"), nullable=False, index=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    horas = db.Column(db.Numeric(6, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    notas = db.Column(db.String(200), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    proyecto = db.relationship("Proyecto", back_populates="registros_horas")
    trabajador = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "trabajador_id": self.trabajador_id,
            "trabajador_nombre": self.trabajador.nombre if self.trabajador else None,
            "horas": float(self.horas),
            "fecha": self.fecha.isoformat(),
            "notas": self.notas,
            "creado_en": self.creado_en.isoformat(),
        }
