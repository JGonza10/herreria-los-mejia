"""Pruebas de humo del PDF de escalera: que se genere, que sea un PDF válido,
y que una captura 3D corrupta no tumbe la generación (el usuario sigue
recibiendo su ficha aunque la captura del navegador haya fallado)."""
import base64

from routes.escalera import calcular_recta, calcular_l, calcular_u, calcular_caracol, ETIQUETAS, NOMBRE_TIPO
from ficha_pdf import generar_ficha_pdf

CASOS = {
    "recta": (calcular_recta, {"altura_total": 2.80}),
    "l": (calcular_l, {"altura_total": 2.80}),
    "u": (calcular_u, {"altura_total": 2.80}),
    "caracol": (calcular_caracol, {"altura_total": 2.80, "diametro_exterior": 1.50}),
}


def test_genera_pdf_valido_para_los_4_tipos():
    for fn, datos in CASOS.values():
        resultado = fn(datos)
        buffer = generar_ficha_pdf(resultado, ETIQUETAS, NOMBRE_TIPO)
        contenido = buffer.read()
        assert contenido.startswith(b"%PDF-")
        assert len(contenido) > 1000


def test_genera_pdf_con_imagen_3d_valida():
    resultado = calcular_recta({"altura_total": 2.80})
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    b64 = "data:image/png;base64," + base64.b64encode(png_1x1).decode()
    buffer = generar_ficha_pdf(resultado, ETIQUETAS, NOMBRE_TIPO, imagen_3d_base64=b64)
    assert buffer.read().startswith(b"%PDF-")


def test_imagen_3d_corrupta_no_tumba_la_generacion():
    resultado = calcular_recta({"altura_total": 2.80})
    buffer = generar_ficha_pdf(resultado, ETIQUETAS, NOMBRE_TIPO, imagen_3d_base64="no-es-base64-valido")
    assert buffer.read().startswith(b"%PDF-")
