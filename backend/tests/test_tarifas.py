"""Pruebas de la administración de tarifas versionadas (Fase 4.2)."""
from extensions import db
from models import Usuario


def _crear_admin_y_loguear(client, app):
    with app.app_context():
        admin = Usuario(nombre="Admin", email="admin@test.com", rol="administrador")
        admin.set_password("passwordadmin123")
        db.session.add(admin)
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "passwordadmin123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def _crear_trabajador_y_loguear(client, app):
    with app.app_context():
        trab = Usuario(nombre="Trab", email="trab@test.com", rol="trabajador")
        trab.set_password("passwordtrab123")
        db.session.add(trab)
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "trab@test.com", "password": "passwordtrab123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def test_crear_cargar_activar_y_duplicar_tarifa(app, client):
    headers = _crear_admin_y_loguear(client, app)

    r = client.post("/api/admin/tarifas", json={"nombre": "Julio 2026", "vigente_desde": "2026-07-01"}, headers=headers)
    assert r.status_code == 201
    tarifa_id = r.get_json()["id"]

    r = client.put(f"/api/admin/tarifas/{tarifa_id}/precios", json={"precios": [
        {"concepto": "material_base", "clave": "hierro", "unidad": "m2", "precio": 1200},
        {"concepto": "acabado", "clave": "hierro", "unidad": "m2", "precio": 250},
    ]}, headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()["precios"]) == 2

    r = client.post(f"/api/admin/tarifas/{tarifa_id}/activar", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["activa"] is True

    r = client.post(f"/api/admin/tarifas/{tarifa_id}/duplicar", json={
        "nombre": "Agosto 2026", "vigente_desde": "2026-08-01", "ajuste_pct": 4,
    }, headers=headers)
    assert r.status_code == 201
    precios = {p["clave"] + p["concepto"]: p["precio"] for p in r.get_json()["precios"]}
    assert precios["hierromaterial_base"] == 1248.0
    assert precios["hierroacabado"] == 260.0
    assert r.get_json()["activa"] is False  # la nueva no se activa sola

    r = client.get("/api/admin/tarifas", headers=headers)
    assert len(r.get_json()) == 2


def test_solo_administrador_puede_gestionar_tarifas(app, client):
    headers = _crear_trabajador_y_loguear(client, app)
    r = client.post("/api/admin/tarifas", json={"nombre": "x", "vigente_desde": "2026-07-01"}, headers=headers)
    assert r.status_code == 403


def test_validaciones_de_tarifa(app, client):
    headers = _crear_admin_y_loguear(client, app)

    r = client.post("/api/admin/tarifas", json={"nombre": "", "vigente_desde": "2026-07-01"}, headers=headers)
    assert r.status_code == 400

    r = client.post("/api/admin/tarifas", json={"nombre": "x", "vigente_desde": "01-07-2026"}, headers=headers)
    assert r.status_code == 400

    r = client.post("/api/admin/tarifas", json={"nombre": "x", "vigente_desde": "2026-07-01"}, headers=headers)
    tarifa_id = r.get_json()["id"]
    r = client.put(f"/api/admin/tarifas/{tarifa_id}/precios", json={
        "precios": [{"concepto": "material_base", "clave": "hierro", "unidad": "m2", "precio": -5}],
    }, headers=headers)
    assert r.status_code == 400

    r = client.get("/api/admin/tarifas/9999", headers=headers)
    assert r.status_code == 404
