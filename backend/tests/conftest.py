import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest

from app import create_app
from extensions import db
from models import PrecioMaterial

PRECIOS_PRUEBA = [
    {"material": "hierro", "precio_base_m2": 1200, "precio_acabado_extra_m2": 250},
    {"material": "aluminio", "precio_base_m2": 1450, "precio_acabado_extra_m2": 300},
    {"material": "vidrio", "precio_base_m2": 1800, "precio_acabado_extra_m2": 400},
]


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        db.create_all()
        db.session.add_all(PrecioMaterial(**p) for p in PRECIOS_PRUEBA)
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
