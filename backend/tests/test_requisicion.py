"""Pruebas de integración de despiece/orden de trabajo/requisición (Fase 5),
usando el flujo real de tarifa + cotización con partidas."""
from datetime import date

from extensions import db
from models import Tarifa, PrecioTarifa, Usuario


def _admin(client, app):
    with app.app_context():
        admin = Usuario(nombre="Admin", email="admin@test.com", rol="administrador")
        admin.set_password("passwordadmin123")
        db.session.add(admin)
        tarifa = Tarifa(nombre="Julio 2026", vigente_desde=date(2026, 7, 1), activa=True)
        db.session.add(tarifa)
        db.session.flush()
        db.session.add_all([
            PrecioTarifa(tarifa_id=tarifa.id, concepto="material_base", clave="hierro", unidad="m2", precio=1200),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="acabado", clave="hierro", unidad="m2", precio=250),
        ])
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "passwordadmin123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def _crear_cotizacion_con_partida(client, headers):
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Juan Perez", "telefono": "5551234567",
        "piezas": [{"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 3.20, "alto_m": 2.40, "con_acabado": True}],
    })
    datos = r.get_json()
    return datos["id"], datos["partidas"][0]["id"]


def test_despiece_de_partida(client, app):
    headers = _admin(client, app)
    _, partida_id = _crear_cotizacion_con_partida(client, headers)

    r = client.post(f"/api/admin/partidas/{partida_id}/despiece", json={"merma_pct_teorica": 7}, headers=headers)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["num_barras"] > 0
    assert "merma_pct_real" in datos


def test_orden_trabajo_pdf(client, app):
    headers = _admin(client, app)
    _, partida_id = _crear_cotizacion_con_partida(client, headers)

    r = client.get(f"/api/admin/partidas/{partida_id}/orden-trabajo.pdf", headers=headers)
    assert r.status_code == 200
    assert r.data.startswith(b"%PDF-")


def test_requisicion_suma_proyectos_activos(client, app):
    headers = _admin(client, app)
    cotizacion_id, _ = _crear_cotizacion_con_partida(client, headers)

    r = client.post(f"/api/admin/cotizaciones/{cotizacion_id}/aprobar", json={}, headers=headers)
    assert r.status_code == 201

    r = client.get("/api/admin/requisicion", headers=headers)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["total_barras_6m"] > 0
    assert len(datos["detalle"]) == 1
