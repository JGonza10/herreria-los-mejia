"""Primitivas de geometría para dibujar una escalera ya calculada — números
puros (metros), sin reportlab ni three.js, para que tanto el PDF como (más
adelante) el 2D/3D de pantalla lean de la misma fuente.

Perfil esquemático: todas las escaleras comparten contrahuella/huella/
num_escalones, así que un mismo perfil lateral (escalones ascendiendo) sirve
para recta, L, U y caracol. No representa el giro en planta de L/U/caracol —
para eso ya existe Escalera3D.jsx en el frontend.
"""

ALTURA_SILUETA_M = 1.70


def perfil_escalones(resultado):
    """resultado: el dict que devuelve cualquiera de las calcular_* de
    routes/escalera.py. Devuelve la lista de escalones como rectángulos
    (x, y, ancho, alto, en metros, origen en la esquina inferior del primer
    escalón) más las dimensiones totales."""
    num_escalones = resultado["num_escalones"]
    contrahuella = resultado["contrahuella"]
    huella = resultado.get("huella") or resultado.get("huella_linea_paso")

    escalones = []
    for i in range(num_escalones):
        escalones.append({
            "x": round(i * huella, 4),
            "y": 0.0,
            "ancho": huella,
            "alto": round((i + 1) * contrahuella, 4),
        })

    return {
        "escalones": escalones,
        "ancho_total_m": round(huella * num_escalones, 4),
        "alto_total_m": round(contrahuella * num_escalones, 4),
    }


def escala_sugerida(alto_total_m):
    """1:20, 1:25 o 1:50 según qué tan grande sea la pieza frente a la
    silueta de referencia, para que quepa en una hoja carta con margen."""
    mayor = max(alto_total_m, ALTURA_SILUETA_M)
    if mayor <= 3:
        return 20
    if mayor <= 5:
        return 25
    return 50
