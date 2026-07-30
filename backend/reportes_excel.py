"""Exporta los reportes de negocio (Fase 8.4) a un solo libro de Excel —
el contador lo va a pedir y XlsxWriter ya está instalado."""
import io
import xlsxwriter


def generar_reportes_excel(costo_real, conversion_tipo, conversion_rango, horas_m2):
    buffer = io.BytesIO()
    libro = xlsxwriter.Workbook(buffer, {"in_memory": True})

    encabezado = libro.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#C2532A", "border": 1})
    celda = libro.add_format({"border": 1})
    celda_alt = libro.add_format({"border": 1, "bg_color": "#FDFCF9"})

    def escribir_tabla(hoja, columnas, filas):
        for col, titulo in enumerate(columnas):
            hoja.write(0, col, titulo, encabezado)
            hoja.set_column(col, col, max(14, len(titulo) + 2))
        for i, fila in enumerate(filas, start=1):
            fmt = celda_alt if i % 2 == 0 else celda
            for col, clave in enumerate(columnas):
                valor = fila.get(clave)
                hoja.write(i, col, valor if valor is not None else "", fmt)

    hoja1 = libro.add_worksheet("Costo real vs cotizado")
    escribir_tabla(hoja1, ["proyecto_id", "titulo", "estado", "cotizado", "costo_material_real",
                           "horas_registradas", "costo_mano_obra_estimado", "costo_real_total",
                           "margen_real", "margen_real_pct"], costo_real)

    hoja2 = libro.add_worksheet("Conversion por tipo")
    escribir_tabla(hoja2, ["tipo", "total", "aprobadas", "tasa_conversion_pct"], conversion_tipo)

    hoja3 = libro.add_worksheet("Conversion por rango")
    escribir_tabla(hoja3, ["rango", "total", "aprobadas", "tasa_conversion_pct"], conversion_rango)

    hoja4 = libro.add_worksheet("Horas por m2")
    escribir_tabla(hoja4, ["proyecto_id", "titulo", "horas_totales", "m2_totales", "horas_por_m2"], horas_m2)

    libro.close()
    buffer.seek(0)
    return buffer
