"""Proyecto.to_dict(vista=...) no debe filtrar datos financieros internos
(costo_material_real, pagos, partidas) a trabajador ni cliente — solo el
administrador los ve. Bug real encontrado al construir la UI de Fase 8."""
from datetime import date

from extensions import db
from models import Tarifa, PrecioTarifa, Usuario


def _admin(client, app):
    with app.app_context():
        admin = Usuario(nombre="Admin", email="admin@test.com", rol="administrador")
        admin.set_password("passwordadmin123")
        db.session.add(admin)
        tarifa = Tarifa(nombre="T", vigente_desde=date(2026, 7, 1), activa=True)
        db.session.add(tarifa)
        db.session.flush()
        db.session.add(PrecioTarifa(tarifa_id=tarifa.id, concepto="material_base", clave="hierro", unidad="m2", precio=1200))
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "passwordadmin123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def _trabajador(client, app):
    with app.app_context():
        trab = Usuario(nombre="Trab", email="trab@test.com", rol="trabajador")
        trab.set_password("passwordtrab123")
        db.session.add(trab)
        db.session.commit()
        trab_id = trab.id
    r = client.post("/api/auth/login", json={"email": "trab@test.com", "password": "passwordtrab123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}, trab_id


def _proyecto_de_cliente(client, headers_admin, headers_clie, trab_id):
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "X", "telefono": "555",
        "piezas": [{"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 2, "alto_m": 2}],
    }, headers=headers_clie)
    cot_id = r.get_json()["id"]
    r = client.post(f"/api/admin/cotizaciones/{cot_id}/aprobar", json={"trabajador_id": trab_id}, headers=headers_admin)
    proyecto_id = r.get_json()["id"]
    client.put(f"/api/admin/proyectos/{proyecto_id}", json={"costo_material_real": 999}, headers=headers_admin)
    return proyecto_id


def test_admin_ve_todo(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    _proyecto_de_cliente(client, headers_admin, headers_admin, trab_id)

    r = client.get("/api/admin/proyectos", headers=headers_admin)
    p = r.get_json()[0]
    assert p["costo_material_real"] == 999.0
    assert "pagos" in p
    assert "partidas" in p


def test_trabajador_no_ve_costos_ni_pagos(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    _proyecto_de_cliente(client, headers_admin, headers_admin, trab_id)

    r = client.get("/api/trabajador/proyectos/asignados", headers=headers_trab)
    p = r.get_json()[0]
    assert "costo_material_real" not in p
    assert "pagos" not in p
    assert "partidas" not in p
    assert "total_horas" in p  # esto sí le sirve a él


def test_cliente_no_ve_costos_ni_pagos_pero_si_saldo(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)

    with app.app_context():
        cliente = Usuario(nombre="Cliente", email="cliente@test.com", rol="cliente")
        cliente.set_password("passwordcliente123")
        db.session.add(cliente)
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "cliente@test.com", "password": "passwordcliente123"})
    headers_clie = {"Authorization": f"Bearer {r.get_json()['token']}"}

    _proyecto_de_cliente(client, headers_admin, headers_clie, trab_id)

    r = client.get("/api/cliente/proyectos", headers=headers_clie)
    p = r.get_json()[0]
    assert "costo_material_real" not in p
    assert "pagos" not in p
    assert "partidas" not in p
    assert "saldo" in p
