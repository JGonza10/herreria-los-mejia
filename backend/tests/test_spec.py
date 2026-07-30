"""Pruebas de la especificación unificada de pieza (Fase 2). Funciones
puras, sin Flask ni base de datos."""
import pytest

from dominio.spec import construir_basico, validar


def test_construir_basico_infiere_sistema_por_material():
    spec = construir_basico("hierro", 3.0, 2.0, False)
    assert spec["sistema"] == "herreria"
    assert spec["version"] == 1
    assert spec["medidas"] == {"ancho_m": 3.0, "alto_m": 2.0}

    assert construir_basico("aluminio", 1, 1, False)["sistema"] == "aluminio"
    assert construir_basico("vidrio", 1, 1, False)["sistema"] == "cristal_templado"


def test_construir_basico_acabado_se_refleja_en_spec():
    assert construir_basico("hierro", 1, 1, False)["acabado"] == "estandar"
    assert construir_basico("hierro", 1, 1, True)["acabado"] == "con_acabado"


def test_spec_basico_es_valido():
    spec = construir_basico("hierro", 3.2, 2.4, True, tipo="porton_corredizo")
    validar(spec)  # no debe lanzar


@pytest.mark.parametrize("mutacion", [
    lambda s: s.pop("version"),
    lambda s: s.update(version="1"),
    lambda s: s.update(tipo=""),
    lambda s: s.update(sistema="madera"),
    lambda s: s["medidas"].update(ancho_m=0),
    lambda s: s["medidas"].update(alto_m=-1),
    lambda s: s.update(piezas=0),
    lambda s: s.update(herrajes=[{"clave": "motor"}]),
])
def test_validar_rechaza_specs_invalidos(mutacion):
    spec = construir_basico("hierro", 3.0, 2.0, False, tipo="porton_corredizo")
    mutacion(spec)
    with pytest.raises(ValueError):
        validar(spec)
