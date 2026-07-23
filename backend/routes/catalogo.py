from flask import Blueprint, jsonify, request
from extensions import db
from models import Producto

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.get("")
def listar_productos():
    material = request.args.get("material")  # hierro | aluminio | vidrio | None
    query = Producto.query.filter_by(activo=True)
    if material:
        query = query.filter_by(material=material)
    productos = query.order_by(Producto.destacado.desc(), Producto.id.asc()).all()
    return jsonify([p.to_dict() for p in productos])


@catalogo_bp.get("/<int:producto_id>")
def obtener_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return jsonify(producto.to_dict())
