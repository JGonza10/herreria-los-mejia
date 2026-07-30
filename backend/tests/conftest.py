import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest

from app import create_app
from extensions import db
from models import PrecioMaterial, TipoTrabajo

PRECIOS_PRUEBA = [
    {"material": "hierro", "precio_base_m2": 1200, "precio_acabado_extra_m2": 250},
    {"material": "aluminio", "precio_base_m2": 1450, "precio_acabado_extra_m2": 300},
    {"material": "vidrio", "precio_base_m2": 1800, "precio_acabado_extra_m2": 400},
]

# Mismo catálogo que seed.py (TIPOS_TRABAJO) — duplicado a propósito en vez
# de importado, para que las pruebas no dependan del script de seed ni de
# sus variables de entorno de contraseñas.
TIPOS_TRABAJO_PRUEBA = [
    {"clave": "porton_corredizo", "nombre": "Portón corredizo", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "porton_abatible", "nombre": "Portón abatible", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "reja_cerca", "nombre": "Reja o cerca", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "proteccion_ventana", "nombre": "Protección para ventana", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "barandal", "nombre": "Barandal", "sistema": "herreria", "unidad": "ml", "altura_referencia_m": 1.00, "modo_dibujo": "estructura"},
    {"clave": "canceleria", "nombre": "Cancelería", "sistema": "aluminio", "unidad": "m2", "modo_dibujo": "cancel", "admite_barrotes": False},
    {"clave": "ventana_aluminio", "nombre": "Ventana de aluminio", "sistema": "aluminio", "unidad": "m2", "modo_dibujo": "cancel", "admite_barrotes": False},
    {"clave": "puerta_cristal_templado", "nombre": "Puerta de cristal templado", "sistema": "cristal_templado", "unidad": "m2", "modo_dibujo": "vidrio", "admite_barrotes": False},
    {"clave": "escalera", "nombre": "Escalera", "sistema": "herreria", "unidad": "ml", "modo_dibujo": "estructura", "admite_barrotes": False},
]


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        db.create_all()
        db.session.add_all(PrecioMaterial(**p) for p in PRECIOS_PRUEBA)
        db.session.add_all(TipoTrabajo(**t) for t in TIPOS_TRABAJO_PRUEBA)
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
