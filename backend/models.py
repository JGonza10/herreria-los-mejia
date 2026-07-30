from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

ROLES = ("administrador", "trabajador", "cliente")
ESTADOS_COTIZACION = ("nueva", "revisada", "aprobada", "rechazada")
ESTADOS_PROYECTO = ("pendiente", "en_proceso", "terminado", "entregado", "cancelado")


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

    producto = db.relationship("Producto")
    proyecto = db.relationship("Proyecto", back_populates="cotizacion", uselist=False)

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
            "tiene_proyecto": self.proyecto is not None,
            "creado_en": self.creado_en.isoformat(),
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
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cotizacion = db.relationship("Cotizacion", back_populates="proyecto")
    cliente = db.relationship("Usuario", foreign_keys=[cliente_id])
    trabajador = db.relationship("Usuario", foreign_keys=[trabajador_id])

    def to_dict(self):
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
        }
