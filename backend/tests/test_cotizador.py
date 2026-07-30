"""Pruebas de referencia para el motor de precios: fijan el total esperado
para casos conocidos. Si el total cambia, la prueba debe tronar — y quien
toque routes/cotizador.py sabe que rompió algo, no lo descubre el cliente.

Nota: hoy todo se cobra por m² (incluido el barandal). Cuando la Fase 2/4
de actualizar.md cambie el barandal a metro lineal, este archivo de pruebas
es el que hay que actualizar primero.
"""
import pytest

from extensions import db
from models import Producto
from routes.cotizador import calcular_precio


def test_porton_hierro_sin_acabado(app):
    with app.app_context():
        m2, total = calcular_precio("hierro", 3.20, 2.40, False)
        assert m2 == 7.68
        assert total == 9216.0


def test_porton_hierro_con_acabado(app):
    with app.app_context():
        m2, total = calcular_precio("hierro", 3.20, 2.40, True)
        assert m2 == 7.68
        assert total == 11136.0


def test_ventana_aluminio_sin_acabado(app):
    with app.app_context():
        m2, total = calcular_precio("aluminio", 1.20, 1.00, False)
        assert m2 == 1.2
        assert total == 1740.0


def test_ventana_aluminio_con_acabado(app):
    with app.app_context():
        m2, total = calcular_precio("aluminio", 1.20, 1.00, True)
        assert m2 == 1.2
        assert total == 2100.0


def test_vidrio_sin_acabado(app):
    with app.app_context():
        m2, total = calcular_precio("vidrio", 2.00, 1.50, False)
        assert m2 == 3.0
        assert total == 5400.0


def test_barandal_aluminio_6m_cobrado_hoy_como_m2(app):
    with app.app_context():
        m2, total = calcular_precio("aluminio", 6.00, 1.00, False)
        assert m2 == 6.0
        assert total == 8700.0


def test_producto_del_catalogo_usa_su_propio_precio_no_el_generico(app):
    with app.app_context():
        producto = Producto(
            nombre="Cancelería de aluminio para balcón",
            material="aluminio",
            descripcion="x",
            precio_referencia_m2=1400,
        )
        db.session.add(producto)
        db.session.commit()

        m2, total = calcular_precio("aluminio", 2.00, 1.00, False, producto)
        assert total == 2800.0

        # El acabado extra siempre sale de la tabla genérica por material,
        # incluso cuando el precio base viene del producto.
        m2, total = calcular_precio("aluminio", 2.00, 1.00, True, producto)
        assert total == 3400.0


def test_material_inexistente_lanza_value_error(app):
    with app.app_context():
        with pytest.raises(ValueError):
            calcular_precio("unicornio", 1.0, 1.0, False)


def test_endpoint_calcular_rechaza_medida_fuera_de_rango(client):
    r = client.post("/api/cotizador/calcular", json={"material": "hierro", "ancho_m": 999, "alto_m": 2.4})
    assert r.status_code == 400
