"""Lista de corte (despiece): de la especificación de una pieza, sacar
cuántos tramos de perfil hacen falta y de qué largo, y cómo acomodarlos en
barras comerciales de 6 m con el menor desperdicio posible (Fase 5.1).

Aplica a piezas rectangulares con relleno de barrotes (portones, rejas,
protecciones de ventana) — no a escalera, que tiene su propia geometría en
dominio/geometria.py, ni a cancelería/vidrio, que no llevan barrotes.

Si el spec no trae separación de barrotes ni travesaños capturados (hoy el
cotizador no pregunta esos datos — ver dominio/spec.py), se usan los
valores por defecto del ejemplo de la Fase 2: 12 cm de separación, sin
travesaños. Es un despiece de referencia, no el definitivo del taller.
"""
LARGO_BARRA_COMERCIAL_M = 6.0
SEPARACION_BARROTES_DEFAULT_CM = 12


def tramos_requeridos(spec, admite_barrotes=True):
    """Lista de tramos (largo en metros) para el marco perimetral, los
    barrotes verticales (si el tipo de trabajo los admite) y los travesaños
    horizontales de una pieza."""
    ancho_m = spec["medidas"]["ancho_m"]
    alto_m = spec["medidas"]["alto_m"]
    piezas = spec.get("piezas", 1)
    estructura = spec.get("estructura") or {}

    tramos = [ancho_m, ancho_m, alto_m, alto_m]  # marco: 2 horizontales + 2 verticales

    if admite_barrotes:
        separacion_cm = estructura.get("separacion_barrotes_cm") or SEPARACION_BARROTES_DEFAULT_CM
        separacion_m = separacion_cm / 100
        num_barrotes = max(0, int(round(ancho_m / separacion_m)) - 1)
        tramos += [alto_m] * num_barrotes

    travesanos = estructura.get("travesanos") or 0
    tramos += [ancho_m] * travesanos

    return [t for t in tramos for _ in range(piezas)]


def optimizar_corte(tramos, largo_barra=LARGO_BARRA_COMERCIAL_M):
    """First-fit decreasing: resuelve el 90% del beneficio en diez líneas,
    no hace falta un solver. Devuelve las barras usadas y la merma real."""
    if any(t > largo_barra for t in tramos):
        raise ValueError(f"Hay un tramo más largo que la barra comercial de {largo_barra:.2f} m.")

    barras = []
    for tramo in sorted(tramos, reverse=True):
        for barra in barras:
            if barra["usado"] + tramo <= largo_barra + 1e-9:
                barra["tramos"].append(tramo)
                barra["usado"] = round(barra["usado"] + tramo, 4)
                break
        else:
            barras.append({"tramos": [tramo], "usado": round(tramo, 4)})

    material_total_m = round(len(barras) * largo_barra, 4)
    material_usado_m = round(sum(t for b in barras for t in b["tramos"]), 4)
    merma_m = round(material_total_m - material_usado_m, 4)
    merma_pct_real = round((merma_m / material_total_m) * 100, 2) if material_total_m else 0.0

    return {
        "barras": [{"tramos": b["tramos"], "usado_m": b["usado"], "sobrante_m": round(largo_barra - b["usado"], 4)} for b in barras],
        "num_barras": len(barras),
        "material_total_m": material_total_m,
        "material_usado_m": material_usado_m,
        "merma_m": merma_m,
        "merma_pct_real": merma_pct_real,
    }


def despiece(spec, merma_pct_teorica=7, admite_barrotes=True):
    """Junta tramos_requeridos + optimizar_corte y compara la merma real
    contra la teórica que se cobró — si el taller cobra 7% y realmente
    desperdicia 14%, está perdiendo dinero en cada trabajo sin saberlo."""
    tramos = tramos_requeridos(spec, admite_barrotes=admite_barrotes)
    resultado = optimizar_corte(tramos)
    resultado["merma_pct_teorica"] = merma_pct_teorica
    resultado["diferencia_merma_pct"] = round(resultado["merma_pct_real"] - merma_pct_teorica, 2)
    return resultado
