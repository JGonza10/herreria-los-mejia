"""Pruebas de referencia para la calculadora de escaleras: una escalera de
2.80 m de altura debe dar siempre el mismo número de escalones y las mismas
advertencias. Son funciones puras (sin Flask, sin base de datos), así que no
usan la fixture de app."""
import pytest

from routes.escalera import calcular_recta, calcular_l, calcular_u, calcular_caracol


def test_recta_2_80m_altura_default():
    r = calcular_recta({"altura_total": 2.80})
    assert r["num_escalones"] == 16
    assert r["contrahuella"] == 0.175
    assert r["huella"] == 0.28
    assert r["longitud_horizontal"] == 4.48
    assert r["inclinacion_grados"] == 32.0
    assert len(r["avisos"]) == 1
    assert "16 escalones" in r["avisos"][0]


def test_l_2_80m_altura_default():
    r = calcular_l({"altura_total": 2.80})
    assert r["num_escalones"] == 16
    assert r["escalones_tramo1"] == 8
    assert r["escalones_tramo2"] == 8
    assert r["espacio_requerido_x"] == 3.14
    assert r["espacio_requerido_y"] == 3.14
    assert r["avisos"] == []


def test_u_2_80m_altura_default():
    r = calcular_u({"altura_total": 2.80})
    assert r["num_escalones"] == 16
    assert r["espacio_requerido_x"] == 1.8
    assert r["espacio_requerido_y"] == 3.14
    assert r["inclinacion_grados"] == 51.3
    assert r["avisos"] == []


def test_caracol_2_80m_diametro_1_50m():
    r = calcular_caracol({"altura_total": 2.80, "diametro_exterior": 1.50})
    assert r["num_escalones"] == 16
    assert r["huella_linea_paso"] == 0.1374
    assert r["angulo_por_escalon"] == 22.5
    # Huella por debajo del mínimo y fuera de Blondel con este diámetro:
    # deben quedar las dos advertencias, más el máximo de escalones y el
    # recordatorio de uso restringido a servicio.
    assert len(r["avisos"]) == 4


def test_caracol_exige_diametro_mayor_al_poste():
    with pytest.raises(ValueError):
        calcular_caracol({"altura_total": 2.80, "diametro_exterior": 0.10, "diametro_poste": 0.10})


def test_altura_negativa_o_cero_es_invalida():
    with pytest.raises(ValueError):
        calcular_recta({"altura_total": 0})


def test_uso_invalido_es_rechazado():
    with pytest.raises(ValueError):
        calcular_recta({"altura_total": 2.80, "uso": "oficina"})
