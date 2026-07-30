"""Pruebas del cobro por sistema (Fase 4.3) y de la cotización con varias
partidas (Fase 4.1): herrería por m², aluminio por perfil (ml) + cristal
(m²), cristal templado con mínimo de fabricación y canteado por perímetro,
y cualquier tipo en 'ml' (barandal) por metro lineal, no por m²."""
from datetime import date

from extensions import db
from models import Tarifa, PrecioTarifa, TipoTrabajo, Usuario
from dominio.spec import construir_basico
from dominio.precios import cotizar_partida


def _crear_tarifa_con_precios(app):
    with app.app_context():
        tarifa = Tarifa(nombre="Julio 2026", vigente_desde=date(2026, 7, 1), activa=True)
        db.session.add(tarifa)
        db.session.flush()
        db.session.add_all([
            PrecioTarifa(tarifa_id=tarifa.id, concepto="material_base", clave="hierro", unidad="m2", precio=1200),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="acabado", clave="hierro", unidad="m2", precio=250),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="perfil", clave="aluminio", unidad="ml", precio=300),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="cristal", clave="vidrio", unidad="m2", precio=900),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="material_base", clave="cristal_templado", unidad="m2", precio=1800),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="canteado", clave="cristal_templado", unidad="ml", precio=80),
            PrecioTarifa(tarifa_id=tarifa.id, concepto="material_base", clave="barandal", unidad="ml", precio=850),
        ])
        db.session.commit()
        return tarifa.id


def _tipo(app, clave):
    with app.app_context():
        return TipoTrabajo.query.filter_by(clave=clave).first()


def test_herreria_se_cobra_por_m2(app):
    tarifa_id = _crear_tarifa_con_precios(app)
    with app.app_context():
        tarifa = Tarifa.query.get(tarifa_id)
        tipo = TipoTrabajo.query.filter_by(clave="porton_corredizo").first()
        spec = construir_basico("hierro", 3.20, 2.40, True, tipo="porton_corredizo", sistema="herreria")
        spec["material"] = "hierro"
        importe, desglose = cotizar_partida(spec, tipo, tarifa)
        assert importe == 11136.0  # 7.68 m2 * (1200+250)
        assert desglose["sistema"] == "herreria"


def test_aluminio_se_cobra_perfil_ml_mas_cristal_m2(app):
    tarifa_id = _crear_tarifa_con_precios(app)
    with app.app_context():
        tarifa = Tarifa.query.get(tarifa_id)
        tipo = TipoTrabajo.query.filter_by(clave="ventana_aluminio").first()
        spec = construir_basico("aluminio", 1.20, 1.00, False, tipo="ventana_aluminio", sistema="aluminio")
        spec["material"] = "aluminio"
        importe, desglose = cotizar_partida(spec, tipo, tarifa)
        # perimetro 4.4m * 300 = 1320 (perfil); 1.2 m2 * 900 = 1080 (cristal)
        assert desglose["importe_perfil"] == 1320.0
        assert desglose["importe_cristal"] == 1080.0
        assert importe == 2400.0


def test_cristal_templado_aplica_minimo_de_fabricacion(app):
    tarifa_id = _crear_tarifa_con_precios(app)
    with app.app_context():
        tarifa = Tarifa.query.get(tarifa_id)
        tipo = TipoTrabajo.query.filter_by(clave="puerta_cristal_templado").first()
        # 40x40 cm = 0.16 m2, muy por debajo del minimo_facturable (1.0 m2 por default del modelo)
        spec = construir_basico("vidrio", 0.40, 0.40, False, tipo="puerta_cristal_templado", sistema="cristal_templado")
        spec["material"] = "vidrio"
        importe, desglose = cotizar_partida(spec, tipo, tarifa)
        assert desglose["area_facturable_m2"] == 1.0
        assert desglose["importe_material"] == 1800.0  # el minimo, no 0.16 * 1800
        assert desglose["importe_canteado"] == round(1.6 * 80, 2)
        assert importe == 1928.0


def test_barandal_se_cobra_por_metro_lineal_no_por_m2(app):
    tarifa_id = _crear_tarifa_con_precios(app)
    with app.app_context():
        tarifa = Tarifa.query.get(tarifa_id)
        tipo = TipoTrabajo.query.filter_by(clave="barandal").first()
        # ancho_m se usa como convención de longitud para tipos 'ml'
        spec = construir_basico("hierro", 6.0, 1.0, False, tipo="barandal", sistema="herreria")
        spec["material"] = "hierro"
        importe, desglose = cotizar_partida(spec, tipo, tarifa)
        assert desglose["unidad"] == "ml"
        assert desglose["longitud_ml"] == 6.0
        assert importe == 5100.0  # 6 * 850, NUNCA 6 * 1 * 1200 (el precio de m2 del hierro)


def test_falta_precio_en_la_tarifa_lanza_value_error(app):
    tarifa_id = _crear_tarifa_con_precios(app)
    with app.app_context():
        tarifa = Tarifa.query.get(tarifa_id)
        # tipo_trabajo=None y sistema desconocido -> cae a herreria con un material sin precio
        spec = construir_basico("madera", 1.0, 1.0, False)
        spec["material"] = "madera"
        import pytest
        with pytest.raises(ValueError):
            cotizar_partida(spec, None, tarifa)


def test_endpoint_solicitar_con_varias_partidas(client, app):
    tarifa_id = _crear_tarifa_con_precios(app)

    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Juan Perez", "telefono": "5551234567", "aplica_iva": True,
        "piezas": [
            {"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 3.20, "alto_m": 2.40, "con_acabado": True},
            {"tipo": "barandal", "material": "hierro", "ancho_m": 6.0, "alto_m": 1.0},
        ],
    })
    assert r.status_code == 201
    datos = r.get_json()
    assert len(datos["partidas"]) == 2
    assert datos["subtotal"] == 11136.0 + 5100.0
    assert datos["iva"] == round(datos["subtotal"] * 0.16, 2)
    assert datos["total"] == round(datos["subtotal"] + datos["iva"], 2)
    assert datos["folio"].startswith("LM-")
    assert datos["vigencia_hasta"] is not None


def test_endpoint_solicitar_sin_tarifa_activa_falla_claro(client):
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Juan", "telefono": "555",
        "piezas": [{"tipo": "porton_corredizo", "material": "hierro", "ancho_m": 3, "alto_m": 2}],
    })
    assert r.status_code == 400
    assert "tarifa activa" in r.get_json()["error"]


def test_endpoint_solicitar_legacy_sin_piezas_sigue_igual(client, app):
    """El frontend actual (Cotizador.jsx) no manda 'piezas' — debe seguir
    funcionando exactamente como antes de la Fase 4."""
    r = client.post("/api/cotizador/solicitar", json={
        "nombre_cliente": "Ana", "telefono": "555", "material": "hierro", "ancho_m": 2, "alto_m": 2,
    })
    assert r.status_code == 201
    datos = r.get_json()
    assert datos["precio_estimado"] == 4800.0  # 4 m2 * 1200 (PrecioMaterial, no Tarifa)
    assert datos["folio"] is None  # el flujo legacy no genera folio
