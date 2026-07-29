"""Genera el registro en Excel de una escalera ya calculada."""
import io
from datetime import datetime
import xlsxwriter

CAMPOS_OCULTOS = {"tipo", "avisos"}


def generar_ficha_excel(resultado, etiquetas, nombre_tipo):
    buffer = io.BytesIO()
    libro = xlsxwriter.Workbook(buffer, {"in_memory": True})
    hoja = libro.add_worksheet("Escalera")

    formato_titulo = libro.add_format({"bold": True, "font_size": 16, "font_color": "#C2532A"})
    formato_sub = libro.add_format({"font_size": 10, "font_color": "#7A756A"})
    formato_encabezado = libro.add_format({
        "bold": True, "font_color": "#FFFFFF", "bg_color": "#C2532A", "border": 1,
    })
    formato_celda = libro.add_format({"border": 1})
    formato_celda_alt = libro.add_format({"border": 1, "bg_color": "#FDFCF9"})
    formato_aviso = libro.add_format({"font_color": "#712B13", "bg_color": "#FAECE7", "border": 1, "text_wrap": True})
    formato_seccion = libro.add_format({"bold": True, "font_size": 12})

    hoja.set_column("A:A", 32)
    hoja.set_column("B:B", 22)

    hoja.write("A1", "LOS MEJÍA", formato_titulo)
    hoja.write("A2", f"Ficha técnica de escalera — {nombre_tipo.get(resultado['tipo'], resultado['tipo'])} · {datetime.now().strftime('%d/%m/%Y')}", formato_sub)

    fila = 3
    avisos = resultado.get("avisos") or []
    if avisos:
        hoja.write(fila, 0, "Advertencias", formato_seccion)
        fila += 1
        for a in avisos:
            hoja.merge_range(fila, 0, fila, 1, a, formato_aviso)
            fila += 1
        fila += 1

    hoja.write(fila, 0, "Datos calculados", formato_seccion)
    fila += 1
    hoja.write(fila, 0, "Dato", formato_encabezado)
    hoja.write(fila, 1, "Valor", formato_encabezado)
    fila += 1

    i = 0
    for clave, etiqueta in etiquetas.items():
        if clave in resultado and clave not in CAMPOS_OCULTOS:
            fmt = formato_celda_alt if i % 2 else formato_celda
            hoja.write(fila, 0, etiqueta, fmt)
            hoja.write(fila, 1, resultado[clave], fmt)
            fila += 1
            i += 1

    libro.close()
    buffer.seek(0)
    return buffer
