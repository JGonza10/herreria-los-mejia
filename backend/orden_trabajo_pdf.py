"""PDF de orden de trabajo para el trabajador: descripción de la pieza,
lista de corte y folio — sin precios, porque el trabajador no necesita
verlos y el cliente no debe verlos si la hoja se queda en la obra.

No incluye el alzado 2D de la pieza todavía: eso depende del dibujo
paramétrico genérico (Fase 6, dominio/geometria.py hoy solo sabe dibujar
escaleras). Cuando exista, es el primer lugar donde conectarlo.
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

COLOR_ASCUA = colors.HexColor("#c2532a")
COLOR_TEXTO = colors.HexColor("#2b2620")
COLOR_TENUE = colors.HexColor("#7a756a")
COLOR_BORDE = colors.HexColor("#e4dfd2")


def generar_orden_trabajo_pdf(cotizacion, partida, despiece_resultado):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=COLOR_ASCUA, fontName="Helvetica-Bold", fontSize=20, spaceAfter=2)
    estilo_sub = ParagraphStyle("sub", parent=estilos["Normal"], textColor=COLOR_TENUE, fontSize=10, spaceAfter=18)
    estilo_seccion = ParagraphStyle("seccion", parent=estilos["Heading2"], textColor=COLOR_TEXTO, fontSize=13, spaceBefore=10, spaceAfter=8)
    estilo_pie = ParagraphStyle("pie", parent=estilos["Normal"], textColor=COLOR_TENUE, fontSize=8, spaceBefore=20)

    elementos = [
        Paragraph("LOS MEJÍA — Orden de trabajo", estilo_titulo),
        Paragraph(
            f"Folio {cotizacion.folio or cotizacion.id} · Cliente: {cotizacion.nombre_cliente} · "
            f"{partida.descripcion or partida.spec.get('tipo', 'pieza')}",
            estilo_sub,
        ),
    ]

    medidas = partida.spec.get("medidas", {})
    elementos.append(Paragraph("Pieza", estilo_seccion))
    elementos.append(Paragraph(
        f"Ancho: {medidas.get('ancho_m', '—')} m &nbsp;&nbsp; Alto: {medidas.get('alto_m', '—')} m &nbsp;&nbsp; "
        f"Piezas: {partida.spec.get('piezas', 1)} &nbsp;&nbsp; Sistema: {partida.spec.get('sistema', '—')}",
        estilos["Normal"],
    ))

    elementos.append(Paragraph("Lista de corte", estilo_seccion))
    filas = [["Barra #", "Tramos (m)", "Usado (m)", "Sobrante (m)"]]
    for i, barra in enumerate(despiece_resultado["barras"], start=1):
        tramos_txt = ", ".join(f"{t:.2f}" for t in barra["tramos"])
        filas.append([str(i), tramos_txt, f"{barra['usado_m']:.2f}", f"{barra['sobrante_m']:.2f}"])

    tabla = Table(filas, colWidths=[2 * cm, 8 * cm, 2.5 * cm, 2.5 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_ASCUA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDE),
        ("TEXTCOLOR", (0, 1), (-1, -1), COLOR_TEXTO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdfcf9")]),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 8))
    elementos.append(Paragraph(
        f"Barras comerciales de 6 m necesarias: <b>{despiece_resultado['num_barras']}</b> &nbsp;&nbsp; "
        f"Merma real: <b>{despiece_resultado['merma_pct_real']}%</b> "
        f"(teórica cobrada: {despiece_resultado['merma_pct_teorica']}%)",
        estilos["Normal"],
    ))

    herrajes = partida.spec.get("herrajes") or []
    if herrajes:
        elementos.append(Paragraph("Herrajes", estilo_seccion))
        for h in herrajes:
            elementos.append(Paragraph(f"• {h.get('clave', '?')} × {h.get('cantidad', 1)}", estilos["Normal"]))

    elementos.append(Paragraph(
        "Esta hoja no lleva precios — es para taller, no para el cliente.",
        estilo_pie,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
