"""Motor de precios. Reubicado desde routes/cotizador.py (Fase 2 de
actualizar.md) para que el cálculo no dependa de Flask y se pueda reutilizar
desde el generador de PDF o un script sin levantar toda la aplicación.

Dos motores conviven a propósito:
- `calcular_precio()`: el original, sigue leyendo PrecioMaterial. Lo usa el
  flujo de una sola pieza de routes/cotizador.py (Cotizador.jsx del
  frontend no ha cambiado).
- `cotizar_partida()`: el nuevo (Fase 4.3), lee de una Tarifa versionada y
  aplica una estrategia de cobro distinta por sistema — herrería sigue por
  m², pero aluminio y cristal templado ya no se calculaban bien con un solo
  precio por m² (ver docstring de la función).
"""
from models import PrecioMaterial, PrecioTarifa


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


def _precio_tarifa(tarifa_id, concepto, clave):
    fila = PrecioTarifa.query.filter_by(tarifa_id=tarifa_id, concepto=concepto, clave=clave).first()
    if not fila:
        raise ValueError(f"Falta el precio de '{concepto}/{clave}' en la tarifa activa.")
    return float(fila.precio)


def cotizar_partida(spec, tipo_trabajo, tarifa):
    """Cotiza una partida según cómo se cobra realmente cada sistema
    (Fase 4.3) — antes todo se cobraba por m², lo cual está bien para
    herrería pero mal para los otros dos:

    - herrería: m² de superficie, ajustado por acabado.
    - aluminio: metros lineales de perfil (perímetro) + m² de cristal — son
      dos precios que se mueven por separado.
    - cristal templado: m² con mínimo de fabricación, más el canteado
      cobrado por perímetro (no por área).

    Sin esto, una ventana de 40×40 cm no cuesta la sexta parte de una de
    1×1 m — el templado tiene mínimo por pieza y el canteado se paga por
    perímetro. Devuelve (importe, desglose)."""
    ancho_m = spec["medidas"]["ancho_m"]
    alto_m = spec["medidas"]["alto_m"]
    piezas = spec.get("piezas", 1)
    area_m2 = round(ancho_m * alto_m, 4)
    perimetro_ml = round(2 * (ancho_m + alto_m), 4)

    sistema = (tipo_trabajo.sistema if tipo_trabajo else None) or spec.get("sistema", "herreria")
    material = spec.get("material") or {"herreria": "hierro", "aluminio": "aluminio", "cristal_templado": "vidrio"}.get(sistema, "hierro")

    # El barandal (y cualquier tipo marcado como 'ml') se cobra por metro
    # lineal, no por m² — la corrección de modelado más importante de esta
    # fase: un barandal de 6 m no es "6 m² con 1 m de altura de referencia",
    # es 6 metros lineales. Por convención, 'ancho_m' guarda la longitud.
    # La clave del precio es el TIPO de trabajo (p. ej. "barandal"), no el
    # material — el precio por metro lineal de un barandal no tiene por qué
    # coincidir con el precio por m² del mismo material en una superficie.
    if tipo_trabajo and tipo_trabajo.unidad == "ml":
        longitud_ml = ancho_m
        precio_ml = _precio_tarifa(tarifa.id, "material_base", tipo_trabajo.clave)
        importe_unitario = round(longitud_ml * precio_ml, 2)
        importe = round(importe_unitario * piezas, 2)
        return importe, {
            "sistema": sistema, "unidad": "ml", "longitud_ml": longitud_ml,
            "precio_ml": precio_ml, "piezas": piezas,
            "importe_unitario": importe_unitario, "importe": importe,
        }

    desglose = {"sistema": sistema, "area_m2": area_m2, "perimetro_ml": perimetro_ml, "piezas": piezas}

    if sistema == "aluminio":
        precio_perfil_ml = _precio_tarifa(tarifa.id, "perfil", "aluminio")
        precio_cristal_m2 = _precio_tarifa(tarifa.id, "cristal", "vidrio")
        importe_perfil = round(perimetro_ml * precio_perfil_ml, 2)
        importe_cristal = round(area_m2 * precio_cristal_m2, 2)
        importe_unitario = round(importe_perfil + importe_cristal, 2)
        desglose.update(
            precio_perfil_ml=precio_perfil_ml, importe_perfil=importe_perfil,
            precio_cristal_m2=precio_cristal_m2, importe_cristal=importe_cristal,
        )

    elif sistema == "cristal_templado":
        minimo_m2 = float(tipo_trabajo.minimo_facturable) if tipo_trabajo and tipo_trabajo.minimo_facturable else 1.0
        area_facturable = max(area_m2, minimo_m2)
        precio_m2 = _precio_tarifa(tarifa.id, "material_base", "cristal_templado")
        precio_canteado_ml = _precio_tarifa(tarifa.id, "canteado", "cristal_templado")
        importe_material = round(area_facturable * precio_m2, 2)
        importe_canteado = round(perimetro_ml * precio_canteado_ml, 2)
        importe_unitario = round(importe_material + importe_canteado, 2)
        desglose.update(
            area_facturable_m2=area_facturable, precio_m2=precio_m2, importe_material=importe_material,
            precio_canteado_ml=precio_canteado_ml, importe_canteado=importe_canteado,
        )

    else:  # herreria (default)
        precio_m2 = _precio_tarifa(tarifa.id, "material_base", material)
        if spec.get("acabado") == "con_acabado":
            precio_m2 += _precio_tarifa(tarifa.id, "acabado", material)
        importe_unitario = round(area_m2 * precio_m2, 2)
        desglose.update(precio_m2=precio_m2)

    importe = round(importe_unitario * piezas, 2)
    desglose["importe_unitario"] = importe_unitario
    desglose["importe"] = importe
    return importe, desglose
