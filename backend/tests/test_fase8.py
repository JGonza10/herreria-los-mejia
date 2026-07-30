"""Pruebas de los números del negocio (Fase 8): registro de horas, costo
real vs. cotizado, tasas de conversión y exportación a Excel."""
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


def _trabajador(client, app):
    with app.app_context():
        trab = Usuario(nombre="Trab", email="trab@test.com", rol="trabajador")
        trab.set_password("passwordtrab123")
        db.session.add(trab)
        db.session.commit()
        trab_id = trab.id
    r = client.post("/api/auth/login", json={"email": "trab@test.com", "password": "passwordtrab123"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}, trab_id


def _proyecto_con_pago(client, headers_admin, trab_id):
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Juan Perez", "telefono": "5551234567",
        "piezas": [{"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 3.20, "alto_m": 2.40, "con_acabado": True}],
    })
    cotizacion_id = r.get_json()["id"]
    r = client.post(f"/api/admin/cotizaciones/{cotizacion_id}/aprobar", json={"trabajador_id": trab_id}, headers=headers_admin)
    proyecto_id = r.get_json()["id"]
    client.post(f"/api/admin/proyectos/{proyecto_id}/pagos", json={"monto": 5000, "fecha": "2026-07-30"}, headers=headers_admin)
    return proyecto_id


def test_trabajador_registra_horas(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    proyecto_id = _proyecto_con_pago(client, headers_admin, trab_id)

    r = client.post(f"/api/trabajador/proyectos/{proyecto_id}/horas", json={"horas": 6, "fecha": "2026-07-30"}, headers=headers_trab)
    assert r.status_code == 201
    assert r.get_json()["horas"] == 6.0

    r = client.post(f"/api/trabajador/proyectos/{proyecto_id}/horas", json={"horas": 3}, headers=headers_trab)
    assert r.status_code == 201


def test_costo_real_vs_cotizado_y_margen(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    proyecto_id = _proyecto_con_pago(client, headers_admin, trab_id)

    client.post(f"/api/trabajador/proyectos/{proyecto_id}/horas", json={"horas": 9, "fecha": "2026-07-30"}, headers=headers_trab)
    r = client.put(f"/api/admin/proyectos/{proyecto_id}", json={"costo_material_real": 6500}, headers=headers_admin)
    assert r.get_json()["costo_material_real"] == 6500.0
    assert r.get_json()["total_horas"] == 9.0

    r = client.get("/api/admin/reportes/costo-real", headers=headers_admin)
    assert r.status_code == 200
    reporte = next(x for x in r.get_json() if x["proyecto_id"] == proyecto_id)
    assert reporte["cotizado"] == 11136.0
    # 9 horas * 120 $/hora = 1080; costo_real_total = 6500 + 1080 = 7580
    assert reporte["costo_mano_obra_estimado"] == 1080.0
    assert reporte["costo_real_total"] == 7580.0
    assert reporte["margen_real"] == round(11136.0 - 7580.0, 2)


def test_costo_real_es_none_sin_captura_manual(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    proyecto_id = _proyecto_con_pago(client, headers_admin, trab_id)

    r = client.get("/api/admin/reportes/costo-real", headers=headers_admin)
    reporte = next(x for x in r.get_json() if x["proyecto_id"] == proyecto_id)
    assert reporte["costo_material_real"] is None
    assert reporte["costo_real_total"] is None
    assert reporte["margen_real"] is None


def test_reporte_conversion_por_tipo_y_rango(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    _proyecto_con_pago(client, headers_admin, trab_id)

    r = client.get("/api/admin/reportes/conversion", headers=headers_admin)
    assert r.status_code == 200
    datos = r.get_json()
    tipo = next(t for t in datos["por_tipo"] if t["tipo"] == "Portón corredizo")
    assert tipo["total"] == 1
    assert tipo["aprobadas"] == 1
    assert tipo["tasa_conversion_pct"] == 100.0

    rango = next(x for x in datos["por_rango_precio"] if x["rango"] == "5000-15000")
    assert rango["total"] == 1


def test_reporte_horas_por_m2(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    proyecto_id = _proyecto_con_pago(client, headers_admin, trab_id)
    client.post(f"/api/trabajador/proyectos/{proyecto_id}/horas", json={"horas": 7.68, "fecha": "2026-07-30"}, headers=headers_trab)

    r = client.get("/api/admin/reportes/horas-por-m2", headers=headers_admin)
    assert r.status_code == 200
    reporte = next(x for x in r.get_json() if x["proyecto_id"] == proyecto_id)
    assert reporte["horas_por_m2"] == 1.0  # 7.68 horas / 7.68 m2


def test_exportar_reportes_a_excel(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    _proyecto_con_pago(client, headers_admin, trab_id)

    r = client.get("/api/admin/reportes/excel", headers=headers_admin)
    assert r.status_code == 200
    assert r.data[:2] == b"PK"  # los .xlsx son un zip


def test_reportes_requieren_admin(client, app):
    headers_trab, _ = _trabajador(client, app)
    r = client.get("/api/admin/reportes/costo-real", headers=headers_trab)
    assert r.status_code == 403
