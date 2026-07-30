"""Alzado 2D acotado de la escalera, en vectores (reportlab.graphics.shapes),
a escala real — no una tabla de números. Se imprime nítido a cualquier
tamaño y el archivo pesa una fracción de lo que pesaría una imagen.

Incluye una silueta humana de 1.70 m a la misma escala: es el detector de
errores de captura más efectivo que existe. Si alguien escribió 320 en vez
de 3.20, la pieza sale veinte veces más alta que la persona y se ve de
inmediato — antes de cortar el material.
"""
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Group, Circle
from reportlab.lib import colors
from reportlab.lib.units import cm

from dominio.geometria import perfil_escalones, escala_sugerida, ALTURA_SILUETA_M

ANCHO_LIENZO_CM = 17
ALTO_LIENZO_CM = 10

COLOR_LINEA = colors.HexColor("#2b2620")
COLOR_RELLENO = colors.HexColor("#fdfcf9")
COLOR_COTA = colors.HexColor("#7a756a")
COLOR_SILUETA = colors.HexColor("#c2532a")


def _silueta_humana(grupo, x_centro, y_base, px_por_m):
    """Silueta simplificada (cabeza + torso) de 1.70 m reales, a la misma
    escala px/m que la escalera — no es decoración, es la referencia."""
    altura_px = ALTURA_SILUETA_M * px_por_m
    radio_cabeza = altura_px * 0.09
    ancho_torso = altura_px * 0.22

    y_torso_base = y_base
    alto_torso = altura_px - 2 * radio_cabeza
    grupo.add(Rect(
        x_centro - ancho_torso / 2, y_torso_base, ancho_torso, alto_torso,
        fillColor=COLOR_SILUETA, strokeColor=None,
    ))
    grupo.add(Circle(
        x_centro, y_torso_base + alto_torso + radio_cabeza, radio_cabeza,
        fillColor=COLOR_SILUETA, strokeColor=None,
    ))


def dibujar_perfil_escalera(resultado):
    """resultado: el dict que devuelve cualquiera de las calcular_* de
    routes/escalera.py. Devuelve un Drawing de reportlab listo para
    insertarse en el documento con doc.build([...])."""
    perfil = perfil_escalones(resultado)
    ancho_total_m = perfil["ancho_total_m"]
    alto_total_m = perfil["alto_total_m"]
    escala = escala_sugerida(alto_total_m)

    margen_cota_m = 0.55
    espacio_silueta_m = 0.9
    ancho_escena_m = ancho_total_m + espacio_silueta_m + margen_cota_m
    alto_escena_m = max(alto_total_m, ALTURA_SILUETA_M) + margen_cota_m

    px_por_m = min(
        (ANCHO_LIENZO_CM * cm - 20) / ancho_escena_m,
        (ALTO_LIENZO_CM * cm - 30) / alto_escena_m,
    )

    d = Drawing(ANCHO_LIENZO_CM * cm, ALTO_LIENZO_CM * cm)
    origen_x = 12
    origen_y = 22

    for escalon in perfil["escalones"]:
        x = origen_x + escalon["x"] * px_por_m
        alto_px = escalon["alto"] * px_por_m
        ancho_px = escalon["ancho"] * px_por_m
        d.add(Rect(
            x, origen_y, ancho_px, alto_px,
            fillColor=COLOR_RELLENO, strokeColor=COLOR_LINEA, strokeWidth=0.8,
        ))

    # Cota de altura total.
    x_cota_altura = origen_x + ancho_total_m * px_por_m + 14
    y_top = origen_y + alto_total_m * px_por_m
    d.add(Line(x_cota_altura, origen_y, x_cota_altura, y_top, strokeColor=COLOR_COTA, strokeWidth=0.6))
    d.add(String(
        x_cota_altura + 4, origen_y + (y_top - origen_y) / 2 - 3,
        f"{alto_total_m:.2f} m", fontSize=8, fillColor=COLOR_COTA,
    ))

    # Cota de longitud horizontal.
    y_cota_ancho = origen_y - 14
    x_right = origen_x + ancho_total_m * px_por_m
    d.add(Line(origen_x, y_cota_ancho, x_right, y_cota_ancho, strokeColor=COLOR_COTA, strokeWidth=0.6))
    d.add(String(
        origen_x + (x_right - origen_x) / 2 - 14, y_cota_ancho - 10,
        f"{ancho_total_m:.2f} m", fontSize=8, fillColor=COLOR_COTA,
    ))

    # Silueta humana de referencia, al lado.
    grupo_silueta = Group()
    x_silueta = origen_x + ancho_total_m * px_por_m + 55
    _silueta_humana(grupo_silueta, x_silueta, origen_y, px_por_m)
    d.add(grupo_silueta)
    d.add(String(x_silueta - 12, origen_y - 10, "1.70 m", fontSize=7, fillColor=COLOR_COTA))

    d.add(String(6, ALTO_LIENZO_CM * cm - 12, f"Alzado — escala 1:{escala}", fontSize=8.5, fillColor=COLOR_LINEA))

    return d
