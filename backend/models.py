from datetime import datetime
from extensions import db


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    material = db.Column(db.String(20), nullable=False)  # hierro | aluminio | vidrio
    descripcion = db.Column(db.Text, nullable=True)
    precio_referencia_m2 = db.Column(db.Numeric(10, 2), nullable=False)
    imagen_url = db.Column(db.String(300), nullable=True)
    destacado = db.Column(db.Boolean, default=False)
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
        }


class PrecioMaterial(db.Model):
    """Precio base por m2 y por acabado, usado por el cotizador."""
    __tablename__ = "precios_material"

    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.String(20), unique=True, nullable=False)  # hierro | aluminio | vidrio
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

    id = db.Column(db.Integer, primary_key=True)
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
    estado = db.Column(db.String(20), default="nueva")  # nueva | contactado | cerrada
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
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
            "creado_en": self.creado_en.isoformat(),
        }
