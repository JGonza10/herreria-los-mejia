"""Los números del negocio (Fase 8): todo lo anterior recopila datos, esta
fase los usa. A diferencia de dominio/, estas funciones sí consultan la
base de datos — son para las rutas de admin, no funciones puras reutilizables
sin contexto de aplicación.
"""
from models import Cotizacion, Partida, Proyecto

# $/hora asumido para valorar la mano de obra registrada — ajustable, no
# hay pantalla de configuración todavía. Con datos reales de RegistroHoras
# acumulados, este número deja de ser una corazonada.
COSTO_HORA_ASUMIDO = 120

RANGOS_PRECIO = [(0, 5000), (5000, 15000), (15000, 30000), (30000, None)]


def costo_real_por_proyecto():
    """Costo estimado contra costo real por proyecto — el único reporte
    que realmente importa, según el propio plan. costo_real_total es None
    mientras el administrador no haya capturado costo_material_real."""
    resultado = []
    for proyecto in Proyecto.query.order_by(Proyecto.creado_en.desc()).all():
        cotizacion = proyecto.cotizacion
        cotizado = float(cotizacion.total) if cotizacion.total is not None else float(cotizacion.precio_estimado)
        costo_material = float(proyecto.costo_material_real) if proyecto.costo_material_real is not None else None
        horas = proyecto.total_horas
        costo_mano_obra = round(horas * COSTO_HORA_ASUMIDO, 2)

        costo_real_total = None
        margen_real = None
        margen_real_pct = None
        if costo_material is not None:
            costo_real_total = round(costo_material + costo_mano_obra, 2)
            margen_real = round(cotizado - costo_real_total, 2)
            margen_real_pct = round(margen_real / cotizado * 100, 2) if cotizado else None

        resultado.append({
            "proyecto_id": proyecto.id,
            "titulo": proyecto.titulo,
            "estado": proyecto.estado,
            "cotizado": cotizado,
            "costo_material_real": costo_material,
            "horas_registradas": horas,
            "costo_mano_obra_estimado": costo_mano_obra,
            "costo_real_total": costo_real_total,
            "margen_real": margen_real,
            "margen_real_pct": margen_real_pct,
        })
    return resultado


def tasa_conversion_por_tipo():
    """Si el 90% de los portones se aprueban y el 20% de los canceles, hay
    algo que corregir en el precio del cancel — o en cómo se presenta."""
    conteo = {}
    for partida in Partida.query.all():
        clave = partida.tipo_trabajo.nombre if partida.tipo_trabajo else "indefinido"
        datos = conteo.setdefault(clave, {"total": 0, "aprobadas": 0})
        datos["total"] += 1
        if partida.cotizacion.estado == "aprobada":
            datos["aprobadas"] += 1

    return [
        {
            "tipo": tipo,
            "total": datos["total"],
            "aprobadas": datos["aprobadas"],
            "tasa_conversion_pct": round(datos["aprobadas"] / datos["total"] * 100, 2) if datos["total"] else 0,
        }
        for tipo, datos in sorted(conteo.items())
    ]


def tasa_conversion_por_rango_precio():
    etiquetas = {f"{a}-{b}" if b else f"{a}+": (a, b) for a, b in RANGOS_PRECIO}
    conteo = {etiqueta: {"total": 0, "aprobadas": 0} for etiqueta in etiquetas}

    for cotizacion in Cotizacion.query.all():
        total = float(cotizacion.total) if cotizacion.total is not None else float(cotizacion.precio_estimado)
        for etiqueta, (a, b) in etiquetas.items():
            if total >= a and (b is None or total < b):
                conteo[etiqueta]["total"] += 1
                if cotizacion.estado == "aprobada":
                    conteo[etiqueta]["aprobadas"] += 1
                break

    return [
        {
            "rango": etiqueta,
            "total": datos["total"],
            "aprobadas": datos["aprobadas"],
            "tasa_conversion_pct": round(datos["aprobadas"] / datos["total"] * 100, 2) if datos["total"] else 0,
        }
        for etiqueta, datos in conteo.items()
    ]


def horas_por_m2():
    """Hoy '320 $/m²' de mano de obra es un número inventado; con dos
    meses de registro deja de serlo."""
    resultado = []
    for proyecto in Proyecto.query.all():
        if not proyecto.registros_horas:
            continue
        m2_total = sum(float(p.cantidad) for p in proyecto.cotizacion.partidas)
        horas = proyecto.total_horas
        resultado.append({
            "proyecto_id": proyecto.id,
            "titulo": proyecto.titulo,
            "horas_totales": horas,
            "m2_totales": round(m2_total, 2),
            "horas_por_m2": round(horas / m2_total, 2) if m2_total else None,
        })
    return resultado
