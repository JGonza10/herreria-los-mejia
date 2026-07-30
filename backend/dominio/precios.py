"""Motor de precios. Reubicado desde routes/cotizador.py (Fase 2 de
actualizar.md) para que el cálculo no dependa de Flask y se pueda reutilizar
desde el generador de PDF o un script sin levantar toda la aplicación.

Sigue tomando el precio de PrecioMaterial (consulta a la base) — la tabla de
tarifas versionadas (Fase 4.2) todavía no existe. Cuando exista, esta
función es la que hay que actualizar primero.
"""
from models import PrecioMaterial


def calcular_precio(material: str, ancho_m: float, alto_m: float, con_acabado: bool, producto=None):
    """Si se pasa `producto` (modelo elegido del catálogo), se usa su propio
    precio_referencia_m2 como base — cada modelo puede costar distinto aunque
    sea del mismo material. Si no, se usa el precio genérico por material
    (propuesta personalizada, sin modelo específico). El extra por acabado
    especial siempre sale de la tabla genérica por material."""
    precio_material = PrecioMaterial.query.filter_by(material=material).first()
    if precio_material is None:
        raise ValueError(f"No hay precio configurado para el material '{material}'")

    m2 = round(ancho_m * alto_m, 2)
    precio_m2 = float(producto.precio_referencia_m2) if producto else float(precio_material.precio_base_m2)
    if con_acabado:
        precio_m2 += float(precio_material.precio_acabado_extra_m2)

    total = round(m2 * precio_m2, 2)
    return m2, total
