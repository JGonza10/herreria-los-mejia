"""Pruebas de Fase 7: aceptación pública, anticipos, fotos de avance,
bitácora, seguimiento/vigencia y agenda."""
from datetime import date, timedelta

from extensions import db
from models import Cotizacion, Proyecto, Tarifa, PrecioTarifa, Usuario


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


def _crear_cotizacion(client):
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Juan Perez", "telefono": "5551234567",
        "piezas": [{"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 3.20, "alto_m": 2.40, "con_acabado": True}],
    })
    return r.get_json()


# --- 7.1 aceptación pública -------------------------------------------------

def test_aceptar_cotizacion_via_link_publico(client, app):
    _admin(client, app)
    datos = _crear_cotizacion(client)

    r = client.get(f"/api/cotizador/publica/{datos['token_publico']}")
    assert r.status_code == 200
    assert r.get_json()["vencida"] is False

    r = client.post(f"/api/cotizador/publica/{datos['token_publico']}/aceptar")
    assert r.status_code == 200
    assert r.get_json()["aceptada_en"] is not None

    # segunda vez debe fallar
    r = client.post(f"/api/cotizador/publica/{datos['token_publico']}/aceptar")
    assert r.status_code == 400


def test_token_invalido_da_404(client):
    r = client.get("/api/cotizador/publica/no-es-un-token-valido")
    assert r.status_code == 404


def test_cotizacion_vencida_no_se_puede_aceptar(client, app):
    _admin(client, app)
    datos = _crear_cotizacion(client)
    with app.app_context():
        c = Cotizacion.query.get(datos["id"])
        c.vigencia_hasta = date.today() - timedelta(days=1)
        db.session.commit()

    r = client.post(f"/api/cotizador/publica/{datos['token_publico']}/aceptar")
    assert r.status_code == 400


# --- 7.2 anticipos -----------------------------------------------------------

def test_no_puede_pasar_a_en_proceso_sin_anticipo(client, app):
    headers = _admin(client, app)
    datos = _crear_cotizacion(client)
    r = client.post(f"/api/admin/cotizaciones/{datos['id']}/aprobar", json={}, headers=headers)
    proyecto_id = r.get_json()["id"]

    r = client.put(f"/api/admin/proyectos/{proyecto_id}", json={"estado": "en_proceso"}, headers=headers)
    assert r.status_code == 400

    r = client.post(f"/api/admin/proyectos/{proyecto_id}/pagos", json={"monto": 5000, "fecha": "2026-07-30"}, headers=headers)
    assert r.status_code == 201
    assert r.get_json()["total_pagado"] == 5000.0

    r = client.put(f"/api/admin/proyectos/{proyecto_id}", json={"estado": "en_proceso"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["estado"] == "en_proceso"


# --- 7.3 fotos de avance ------------------------------------------------------

def test_trabajador_sube_foto_de_avance(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    datos = _crear_cotizacion(client)
    r = client.post(f"/api/admin/cotizaciones/{datos['id']}/aprobar", json={"trabajador_id": trab_id}, headers=headers_admin)
    proyecto_id = r.get_json()["id"]

    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8ffff3f0005fe02fea1399ba50000000049454e44ae426082"
    )
    import io
    r = client.post(
        f"/api/trabajador/proyectos/{proyecto_id}/fotos",
        data={"imagen": (io.BytesIO(png), "avance.png"), "notas": "marco listo"},
        headers=headers_trab, content_type="multipart/form-data",
    )
    assert r.status_code == 201
    assert r.get_json()["notas"] == "marco listo"


def test_otro_trabajador_no_puede_subir_foto_de_proyecto_ajeno(client, app):
    headers_admin = _admin(client, app)
    headers_trab, trab_id = _trabajador(client, app)
    with app.app_context():
        otro = Usuario(nombre="Otro", email="otro@test.com", rol="trabajador")
        otro.set_password("passwordotro123")
        db.session.add(otro)
        db.session.commit()
    r_otro = client.post("/api/auth/login", json={"email": "otro@test.com", "password": "passwordotro123"})
    headers_otro = {"Authorization": f"Bearer {r_otro.get_json()['token']}"}

    datos = _crear_cotizacion(client)
    r = client.post(f"/api/admin/cotizaciones/{datos['id']}/aprobar", json={"trabajador_id": trab_id}, headers=headers_admin)
    proyecto_id = r.get_json()["id"]

    import io
    r = client.post(
        f"/api/trabajador/proyectos/{proyecto_id}/fotos",
        data={"imagen": (io.BytesIO(b"x"), "x.png")},
        headers=headers_otro, content_type="multipart/form-data",
    )
    assert r.status_code == 403


# --- 7.4 vigencia y seguimiento ----------------------------------------------

def test_seguimiento_agrupa_por_dias_sin_respuesta(client, app):
    headers = _admin(client, app)
    datos = _crear_cotizacion(client)
    with app.app_context():
        from datetime import datetime, timedelta as td
        c = Cotizacion.query.get(datos["id"])
        c.creado_en = datetime.utcnow() - td(days=8)
        db.session.commit()

    r = client.get("/api/admin/cotizaciones/seguimiento", headers=headers)
    assert r.status_code == 200
    ids_7_dias = [c["id"] for c in r.get_json()["7_dias"]]
    assert datos["id"] in ids_7_dias


def test_revivir_cotizacion_vencida_recalcula_con_tarifa_activa(client, app):
    headers = _admin(client, app)
    datos = _crear_cotizacion(client)
    with app.app_context():
        c = Cotizacion.query.get(datos["id"])
        c.vigencia_hasta = date.today() - timedelta(days=5)
        c.estado = "vencida"
        db.session.commit()

    r = client.post(f"/api/admin/cotizaciones/{datos['id']}/revivir", headers=headers)
    assert r.status_code == 200
    revivida = r.get_json()
    assert revivida["estado"] == "nueva"
    assert revivida["vigencia_hasta"] > date.today().isoformat()


# --- 7.5 agenda ---------------------------------------------------------------

def test_agenda_reporta_semana_del_proyecto_aprobado(client, app):
    headers = _admin(client, app)
    datos = _crear_cotizacion(client)
    r = client.post(f"/api/admin/cotizaciones/{datos['id']}/aprobar", json={}, headers=headers)
    assert r.get_json()["fecha_estimada_entrega"] is not None

    r = client.get("/api/admin/agenda", headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) >= 1


# --- 7.6 bitácora --------------------------------------------------------------

def test_bitacora_registra_cambio_de_precio_y_activacion(client, app):
    headers = _admin(client, app)

    r = client.post("/api/admin/tarifas", json={"nombre": "Agosto 2026", "vigente_desde": "2026-08-01"}, headers=headers)
    tarifa_id = r.get_json()["id"]
    client.put(f"/api/admin/tarifas/{tarifa_id}/precios", json={
        "precios": [{"concepto": "material_base", "clave": "hierro", "unidad": "m2", "precio": 1300}],
    }, headers=headers)
    client.post(f"/api/admin/tarifas/{tarifa_id}/activar", headers=headers)

    r = client.get("/api/admin/bitacora", headers=headers)
    assert r.status_code == 200
    acciones = {reg["accion"] for reg in r.get_json()}
    assert "activacion" in acciones
    assert "cambio_precio" in acciones


def test_bitacora_filtra_por_entidad(client, app):
    headers = _admin(client, app)
    r = client.get("/api/admin/bitacora?entidad=tarifa", headers=headers)
    assert r.status_code == 200
    assert all(reg["entidad"] == "tarifa" for reg in r.get_json())

    r = client.get("/api/admin/bitacora?entidad=proyecto", headers=headers)
    assert r.get_json() == []
