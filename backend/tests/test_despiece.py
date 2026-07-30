"""Pruebas de la lista de corte (Fase 5.1): tramos requeridos, optimización
de corte (first-fit decreasing) y comparación de merma real vs. teórica."""
import pytest

from dominio.despiece import tramos_requeridos, optimizar_corte, despiece


def test_tramos_requeridos_incluye_marco_y_barrotes():
    spec = {"medidas": {"ancho_m": 3.20, "alto_m": 2.40}, "piezas": 1, "estructura": {}}
    tramos = tramos_requeridos(spec)
    # marco: 2x3.20 + 2x2.40, más barrotes verticales cada 12 cm por defecto
    assert tramos.count(3.20) == 2
    assert tramos.count(2.40) >= 3  # 2 del marco + al menos 1 barrote


def test_sin_barrotes_cuando_el_tipo_no_los_admite():
    spec = {"medidas": {"ancho_m": 3.20, "alto_m": 2.40}, "piezas": 1, "estructura": {}}
    tramos = tramos_requeridos(spec, admite_barrotes=False)
    assert tramos == [3.20, 3.20, 2.40, 2.40]


def test_piezas_multiplica_los_tramos():
    spec = {"medidas": {"ancho_m": 1.0, "alto_m": 1.0}, "piezas": 3, "estructura": {}}
    tramos = tramos_requeridos(spec, admite_barrotes=False)
    assert len(tramos) == 4 * 3


def test_optimizar_corte_acomoda_sin_pasarse_de_la_barra():
    resultado = optimizar_corte([3.2, 3.2, 2.4, 2.4, 2.4, 2.4])
    for barra in resultado["barras"]:
        assert barra["usado_m"] <= 6.0 + 1e-9
    assert resultado["material_usado_m"] == sum([3.2, 3.2, 2.4, 2.4, 2.4, 2.4])


def test_tramo_mas_largo_que_la_barra_lanza_error():
    with pytest.raises(ValueError):
        optimizar_corte([8.0])


def test_despiece_compara_merma_real_contra_teorica():
    spec = {"medidas": {"ancho_m": 3.20, "alto_m": 2.40}, "piezas": 1, "estructura": {}}
    resultado = despiece(spec, merma_pct_teorica=7)
    assert resultado["merma_pct_teorica"] == 7
    assert resultado["diferencia_merma_pct"] == round(resultado["merma_pct_real"] - 7, 2)
