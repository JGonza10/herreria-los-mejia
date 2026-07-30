"""Pruebas de la simulación de cotización (Fase 4.4): no debe guardar nada,
y el margen que reporta es sobre venta, no sobre costo."""
from extensions import db
from models import Cotizacion, Usuario


def _crear_admin_y_loguear(client, app):
    with app.app_context():
        admin = Usuario(nombre="Admin", email="admin@test.com", rol="administrador")
        admin.set_password("passwordadmin123")
        db.session.add(admin)
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "passwordadmin123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def _crear_cotizacion(app):
    with app.app_context():
        c = Cotizacion(
            nombre_cliente="X", telefono="555", material="hierro",
            ancho_m=2, alto_m=2, metros_cuadrados=4, precio_estimado=4800, subtotal=4800, total=4800,
        )
        db.session.add(c)
        db.session.commit()
        return c.id


def test_simular_no_guarda_nada(client, app):
    headers = _crear_admin_y_loguear(client, app)
    cid = _crear_cotizacion(app)

    r = client.post(f"/api/admin/cotizaciones/{cid}/simular", json={
        "mano_obra": 500, "utilidad_pct": 25, "aplica_iva": True,
    }, headers=headers)
    assert r.status_code == 200

    with app.app_context():
        c = Cotizacion.query.get(cid)
        assert float(c.subtotal) == 4800.0  # no cambió


def test_margen_es_sobre_venta_no_sobre_costo(client, app):
    headers = _crear_admin_y_loguear(client, app)
    cid = _crear_cotizacion(app)

    r = client.post(f"/api/admin/cotizaciones/{cid}/simular", json={"utilidad_pct": 25}, headers=headers)
    datos = r.get_json()
    # 25% de utilidad sobre costo equivale a 20% de margen sobre venta.
    assert datos["margen_sobre_venta_pct"] == 20.0
    assert datos["utilidad_pct"] == 25.0


def test_estimado_es_rango_no_numero_exacto(client, app):
    headers = _crear_admin_y_loguear(client, app)
    cid = _crear_cotizacion(app)

    r = client.post(f"/api/admin/cotizaciones/{cid}/simular", json={}, headers=headers)
    datos = r.get_json()
    assert datos["estimado_cliente_min"] < datos["total"] < datos["estimado_cliente_max"]


def test_simular_requiere_admin(client, app):
    with app.app_context():
        trab = Usuario(nombre="T", email="t@test.com", rol="trabajador")
        trab.set_password("passwordtrab123")
        db.session.add(trab)
        db.session.commit()
    r = client.post("/api/auth/login", json={"email": "t@test.com", "password": "passwordtrab123"})
    headers = {"Authorization": f"Bearer {r.get_json()['token']}"}

    cid = _crear_cotizacion(app)
    r = client.post(f"/api/admin/cotizaciones/{cid}/simular", json={}, headers=headers)
    assert r.status_code == 403
