"""Genera la ficha técnica en PDF de una escalera ya calculada."""
import base64
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from ficha_dibujo import dibujar_perfil_escalera

COLOR_ASCUA = colors.HexColor("#c2532a")
COLOR_TEXTO = colors.HexColor("#2b2620")
COLOR_TENUE = colors.HexColor("#7a756a")
COLOR_BORDE = colors.HexColor("#e4dfd2")
COLOR_AVISO = colors.HexColor("#faece7")
COLOR_AVISO_TEXTO = colors.HexColor("#712b13")

CAMPOS_OCULTOS = {"tipo", "avisos"}


def generar_ficha_pdf(resultado, etiquetas, nombre_tipo, imagen_3d_base64=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=COLOR_ASCUA, fontName="Helvetica-Bold", fontSize=20, spaceAfter=2)
    estilo_sub = ParagraphStyle("sub", parent=estilos["Normal"], textColor=COLOR_TENUE, fontSize=10, spaceAfter=18)
    estilo_seccion = ParagraphStyle("seccion", parent=estilos["Heading2"], textColor=COLOR_TEXTO, fontSize=13, spaceBefore=6, spaceAfter=8)
    estilo_aviso = ParagraphStyle("aviso", parent=estilos["Normal"], textColor=COLOR_AVISO_TEXTO, fontSize=9.5, leading=13)
    estilo_pie = ParagraphStyle("pie", parent=estilos["Normal"], textColor=COLOR_TENUE, fontSize=8, spaceBefore=24)

    elementos = []
    elementos.append(Paragraph("LOS MEJÍA", estilo_titulo))
    elementos.append(Paragraph(
        f"Ficha técnica de escalera — {nombre_tipo.get(resultado['tipo'], resultado['tipo'])} · "
        f"{datetime.now().strftime('%d/%m/%Y')}",
        estilo_sub,
    ))

    # Alzado 2D acotado, a escala real, con la silueta de 1.70 m de
    # referencia — se recalcula en el servidor, nunca se confía en un
    # dibujo hecho en el cliente.
    elementos.append(Paragraph("Alzado", estilo_seccion))
    elementos.append(dibujar_perfil_escalera(resultado))

    if imagen_3d_base64:
        try:
            datos_imagen = base64.b64decode(imagen_3d_base64.split(",")[-1])
            imagen = Image(io.BytesIO(datos_imagen), width=9 * cm, height=9 * 380 / 700 * cm)
            imagen.hAlign = "LEFT"
            elementos.append(Spacer(1, 6))
            elementos.append(Paragraph("Vista 3D", estilo_seccion))
            elementos.append(imagen)
        except Exception:
            pass  # una captura corrupta no debe tumbar la generación del PDF

    elementos.append(Spacer(1, 10))

    # Avisos normativos, si los hay
    avisos = resultado.get("avisos") or []
    if avisos:
        elementos.append(Paragraph("Advertencias", estilo_seccion))
        for a in avisos:
            elementos.append(Paragraph(f"⚠ {a}", estilo_aviso))
            elementos.append(Spacer(1, 4))
        elementos.append(Spacer(1, 12))

    # Tabla de datos calculados
    elementos.append(Paragraph("Datos calculados", estilo_seccion))
    filas = [["Dato", "Valor"]]
    for clave, etiqueta in etiquetas.items():
        if clave in resultado and clave not in CAMPOS_OCULTOS:
            filas.append([etiqueta, str(resultado[clave])])

    tabla = Table(filas, colWidths=[9 * cm, 6 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_ASCUA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDE),
        ("TEXTCOLOR", (0, 1), (-1, -1), COLOR_TEXTO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdfcf9")]),
    ]))
    elementos.append(tabla)

    elementos.append(Paragraph(
        "<b>Esta ficha no incluye:</b> obra civil, resane, pintura de muro, "
        "ni instalaciones eléctricas — salvo que se indique explícitamente. "
        "Vigente 30 días a partir de la fecha de emisión.",
        ParagraphStyle("no_incluye", parent=estilos["Normal"], textColor=COLOR_TEXTO, fontSize=9, spaceBefore=14, spaceAfter=6),
    ))

    elementos.append(Paragraph(
        "Calculadora de apoyo para taller — no sustituye una revisión estructural "
        "certificada. Validado contra la Ley de Blondel y el Reglamento de "
        "Construcciones (CDMX).",
        estilo_pie,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
