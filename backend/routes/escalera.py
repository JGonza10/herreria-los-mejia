"""Calculadora de escaleras metálicas — Recta, en L, en U y Caracol.

Fuentes normativas usadas para las validaciones:
- Reglamento de Construcciones para el Distrito Federal (CDMX): huella
  mínima 25 cm, contrahuella máxima 18 cm (20 cm en escaleras de servicio),
  ancho mínimo 0.90 m en vivienda (0.60 m en servicio), máximo 15 escalones
  seguidos sin descanso, barandal mínimo 90 cm de altura, y escaleras de
  caracol permitidas solo para circulación de servicio con diámetro mínimo
  de 1.20 m.
- Ley de Blondel (regla ergonómica estándar, citada también por las guías
  mexicanas de diseño): 2×contrahuella + huella debe quedar entre 60 y 65 cm.

Esto es una calculadora de apoyo para cotizar/fabricar en taller, no un
cálculo estructural certificado — si un proyecto específico cae bajo un
reglamento municipal distinto al de CDMX, hay que confirmarlo aparte.
"""
import math
from flask import Blueprint, jsonify, request
from auth import requiere_rol

escalera_bp = Blueprint("escalera", __name__)

# --- Constantes normativas -------------------------------------------------
CONTRAHUELLA_MIN = 0.10
CONTRAHUELLA_MAX_VIVIENDA = 0.18
CONTRAHUELLA_MAX_SERVICIO = 0.20
HUELLA_MIN = 0.25
BLONDEL_MIN = 0.60
BLONDEL_MAX = 0.65
BLONDEL_IDEAL = 0.63
ANCHO_MIN_VIVIENDA = 0.90
ANCHO_MIN_SERVICIO = 0.60
MAX_ESCALONES_SIN_DESCANSO = 15
BARANDAL_MIN = 0.90
CARACOL_DIAMETRO_MIN = 1.20

TIPOS_VALIDOS = ("recta", "l", "u", "caracol")


# --- Utilidades comunes ------------------------------------------------------
def _contrahuella_maxima(uso):
    return CONTRAHUELLA_MAX_SERVICIO if uso == "servicio" else CONTRAHUELLA_MAX_VIVIENDA


def _ancho_minimo(uso):
    return ANCHO_MIN_SERVICIO if uso == "servicio" else ANCHO_MIN_VIVIENDA


def calcular_escalones(altura_total, contrahuella_deseada, uso):
    """Reparte la altura total en escalones de contrahuella lo más cercana
    posible a la deseada (o a 0.18 m por defecto), sin pasarse del máximo
    normativo."""
    objetivo = contrahuella_deseada or CONTRAHUELLA_MAX_VIVIENDA
    objetivo = min(objetivo, _contrahuella_maxima(uso))
    num_escalones = max(1, math.ceil(altura_total / objetivo))
    contrahuella_real = altura_total / num_escalones
    return num_escalones, contrahuella_real


def huella_por_blondel(contrahuella):
    """huella = 0.63 - 2*contrahuella (despejado de la Ley de Blondel),
    nunca por debajo del mínimo normativo de 25 cm."""
    return max(HUELLA_MIN, round(BLONDEL_IDEAL - 2 * contrahuella, 4))


def validar_comunes(contrahuella, huella, ancho, uso, escalones_por_tramo):
    """Devuelve una lista de advertencias (texto) si algo no cumple los
    mínimos normativos. Lista vacía = todo en regla."""
    avisos = []
    max_contra = _contrahuella_maxima(uso)
    if contrahuella < CONTRAHUELLA_MIN or contrahuella > max_contra:
        avisos.append(
            f"Contrahuella de {contrahuella*100:.1f} cm fuera del rango normativo "
            f"({CONTRAHUELLA_MIN*100:.0f}–{max_contra*100:.0f} cm)."
        )
    if huella < HUELLA_MIN:
        avisos.append(f"Huella de {huella*100:.1f} cm por debajo del mínimo normativo (25 cm).")

    blondel = 2 * contrahuella + huella
    if not (BLONDEL_MIN <= blondel <= BLONDEL_MAX):
        avisos.append(
            f"2×contrahuella + huella = {blondel*100:.1f} cm, fuera del rango cómodo "
            f"según la Ley de Blondel (60–65 cm)."
        )

    ancho_min = _ancho_minimo(uso)
    if ancho < ancho_min:
        avisos.append(f"Ancho de {ancho*100:.0f} cm por debajo del mínimo para uso {uso} ({ancho_min*100:.0f} cm).")

    for tramo in escalones_por_tramo:
        if tramo > MAX_ESCALONES_SIN_DESCANSO:
            avisos.append(
                f"Un tramo de {tramo} escalones seguidos supera el máximo de "
                f"{MAX_ESCALONES_SIN_DESCANSO} sin descanso — se recomienda meter un descanso."
            )
    return avisos


def _leer_comun(data):
    altura_total = float(data["altura_total"])
    ancho = float(data.get("ancho") or ANCHO_MIN_VIVIENDA)
    uso = data.get("uso") or "vivienda"
    contrahuella_deseada = data.get("contrahuella_deseada")
    contrahuella_deseada = float(contrahuella_deseada) if contrahuella_deseada else None
    if altura_total <= 0:
        raise ValueError("La altura total debe ser mayor a 0.")
    if uso not in ("vivienda", "servicio"):
        raise ValueError("uso debe ser 'vivienda' o 'servicio'.")
    return altura_total, ancho, uso, contrahuella_deseada


# --- Cálculo por tipo --------------------------------------------------------
def calcular_recta(data):
    altura_total, ancho, uso, contrahuella_deseada = _leer_comun(data)
    espacio_horizontal = data.get("espacio_horizontal")
    espacio_horizontal = float(espacio_horizontal) if espacio_horizontal else None

    num_escalones, contrahuella = calcular_escalones(altura_total, contrahuella_deseada, uso)
    huella = huella_por_blondel(contrahuella)

    avisos = []
    if espacio_horizontal:
        huella_disponible = espacio_horizontal / num_escalones
        if huella_disponible < huella:
            huella = huella_disponible
            if huella < HUELLA_MIN:
                avisos.append(
                    f"El espacio horizontal disponible obliga a una huella de {huella*100:.1f} cm, "
                    f"por debajo del mínimo normativo (25 cm)."
                )

    longitud = round(huella * num_escalones, 3)
    inclinacion = round(math.degrees(math.atan2(altura_total, longitud)), 1)

    avisos += validar_comunes(contrahuella, huella, ancho, uso, [num_escalones])

    return {
        "tipo": "recta",
        "num_escalones": num_escalones,
        "contrahuella": round(contrahuella, 4),
        "huella": round(huella, 4),
        "longitud_horizontal": longitud,
        "inclinacion_grados": inclinacion,
        "ancho": ancho,
        "avisos": avisos,
    }


def _dividir_tramos(num_escalones):
    tramo1 = math.ceil(num_escalones / 2)
    tramo2 = num_escalones - tramo1
    return tramo1, tramo2


def calcular_l(data):
    altura_total, ancho, uso, contrahuella_deseada = _leer_comun(data)
    num_escalones, contrahuella = calcular_escalones(altura_total, contrahuella_deseada, uso)
    huella = huella_por_blondel(contrahuella)

    tramo1, tramo2 = _dividir_tramos(num_escalones)
    longitud_tramo1 = round(huella * tramo1, 3)
    longitud_tramo2 = round(huella * tramo2, 3)
    # Descanso cuadrado del ancho de la escalera, en la esquina del giro de 90°.
    espacio_x = round(longitud_tramo1 + ancho, 3)
    espacio_y = round(longitud_tramo2 + ancho, 3)
    inclinacion = round(math.degrees(math.atan2(altura_total, longitud_tramo1 + longitud_tramo2)), 1)

    avisos = validar_comunes(contrahuella, huella, ancho, uso, [tramo1, tramo2])

    return {
        "tipo": "l",
        "num_escalones": num_escalones,
        "escalones_tramo1": tramo1,
        "escalones_tramo2": tramo2,
        "contrahuella": round(contrahuella, 4),
        "huella": round(huella, 4),
        "longitud_tramo1": longitud_tramo1,
        "longitud_tramo2": longitud_tramo2,
        "espacio_requerido_x": espacio_x,
        "espacio_requerido_y": espacio_y,
        "inclinacion_grados": inclinacion,
        "ancho": ancho,
        "avisos": avisos,
    }


def calcular_u(data):
    altura_total, ancho, uso, contrahuella_deseada = _leer_comun(data)
    num_escalones, contrahuella = calcular_escalones(altura_total, contrahuella_deseada, uso)
    huella = huella_por_blondel(contrahuella)

    tramo1, tramo2 = _dividir_tramos(num_escalones)
    longitud_tramo = round(huella * max(tramo1, tramo2), 3)
    # Descanso a todo lo ancho de los dos tramos, uno junto al otro.
    espacio_x = round(2 * ancho, 3)
    espacio_y = round(longitud_tramo + ancho, 3)
    inclinacion = round(math.degrees(math.atan2(altura_total, longitud_tramo)), 1)

    avisos = validar_comunes(contrahuella, huella, ancho, uso, [tramo1, tramo2])

    return {
        "tipo": "u",
        "num_escalones": num_escalones,
        "escalones_tramo1": tramo1,
        "escalones_tramo2": tramo2,
        "contrahuella": round(contrahuella, 4),
        "huella": round(huella, 4),
        "longitud_tramo": longitud_tramo,
        "espacio_requerido_x": espacio_x,
        "espacio_requerido_y": espacio_y,
        "inclinacion_grados": inclinacion,
        "ancho": ancho,
        "avisos": avisos,
    }


def calcular_caracol(data):
    altura_total, _ancho_no_usado, uso, contrahuella_deseada = _leer_comun(data)
    diametro_exterior = float(data["diametro_exterior"])
    diametro_poste = float(data.get("diametro_poste") or 0.10)
    angulo_giro_total = float(data.get("angulo_giro_total") or 360)

    if diametro_exterior <= diametro_poste:
        raise ValueError("El diámetro exterior debe ser mayor al diámetro del poste central.")

    # En caracol, servicio es lo normal (uso principal está restringido por
    # reglamento — ver aviso más abajo).
    uso = uso or "servicio"
    num_escalones, contrahuella = calcular_escalones(altura_total, contrahuella_deseada, uso)
    angulo_por_escalon = round(angulo_giro_total / num_escalones, 2)

    radio_exterior = diametro_exterior / 2
    radio_poste = diametro_poste / 2
    # Huella medida en la "línea de paso", a 40 cm hacia adentro del borde
    # exterior (criterio de "escalera compensada" del Reglamento de
    # Construcciones CDMX), sin invadir el poste central.
    radio_linea_paso = max(radio_poste + 0.05, radio_exterior - 0.40)
    huella_linea_paso = round(math.radians(angulo_por_escalon) * radio_linea_paso, 4)

    longitud_linea_paso = round(math.radians(angulo_giro_total) * radio_linea_paso, 3)
    inclinacion = round(math.degrees(math.atan2(altura_total, longitud_linea_paso)), 1)

    avisos = validar_comunes(contrahuella, huella_linea_paso, diametro_exterior, "servicio", [num_escalones])
    # El ancho normativo no aplica igual en caracol (usa diámetro), así que
    # descartamos el aviso de "ancho" genérico y ponemos el de diámetro real.
    avisos = [a for a in avisos if "Ancho de" not in a]
    if diametro_exterior < CARACOL_DIAMETRO_MIN:
        avisos.append(
            f"Diámetro de {diametro_exterior:.2f} m por debajo del mínimo normativo (1.20 m). "
            f"Las escaleras de caracol solo están permitidas para circulación de servicio."
        )
    else:
        avisos.append(
            "Recuerda: las escaleras de caracol solo están permitidas para circulación de "
            "servicio según el Reglamento de Construcciones (CDMX), no como escalera principal."
        )

    return {
        "tipo": "caracol",
        "num_escalones": num_escalones,
        "contrahuella": round(contrahuella, 4),
        "huella_linea_paso": huella_linea_paso,
        "angulo_por_escalon": angulo_por_escalon,
        "angulo_giro_total": angulo_giro_total,
        "diametro_exterior": diametro_exterior,
        "diametro_poste": diametro_poste,
        "inclinacion_grados": inclinacion,
        "avisos": avisos,
    }


CALCULADORAS = {
    "recta": calcular_recta,
    "l": calcular_l,
    "u": calcular_u,
    "caracol": calcular_caracol,
}

ETIQUETAS = {
    "num_escalones": "Número de escalones",
    "contrahuella": "Contrahuella (m)",
    "huella": "Huella (m)",
    "huella_linea_paso": "Huella en línea de paso (m)",
    "longitud_horizontal": "Longitud horizontal (m)",
    "inclinacion_grados": "Inclinación (°)",
    "ancho": "Ancho (m)",
    "escalones_tramo1": "Escalones tramo 1",
    "escalones_tramo2": "Escalones tramo 2",
    "longitud_tramo1": "Longitud tramo 1 (m)",
    "longitud_tramo2": "Longitud tramo 2 (m)",
    "longitud_tramo": "Longitud de cada tramo (m)",
    "espacio_requerido_x": "Espacio requerido X (m)",
    "espacio_requerido_y": "Espacio requerido Y (m)",
    "diametro_exterior": "Diámetro exterior (m)",
    "diametro_poste": "Diámetro del poste central (m)",
    "angulo_por_escalon": "Ángulo por escalón (°)",
    "angulo_giro_total": "Ángulo de giro total (°)",
}

NOMBRE_TIPO = {"recta": "Recta", "l": "En L", "u": "En U", "caracol": "Caracol"}


def _calcular_o_error(data):
    """Devuelve (resultado, None) o (None, (jsonify, status)) — para
    compartir la validación entre /calcular y /pdf sin duplicar el try/except."""
    tipo = (data.get("tipo") or "").lower()
    if tipo not in TIPOS_VALIDOS:
        return None, (jsonify({"error": f"tipo debe ser uno de: {', '.join(TIPOS_VALIDOS)}"}), 400)
    try:
        return CALCULADORAS[tipo](data), None
    except (KeyError, TypeError):
        return None, (jsonify({"error": "Faltan datos requeridos para este tipo de escalera."}), 400)
    except ValueError as e:
        return None, (jsonify({"error": str(e)}), 400)


@escalera_bp.post("/calcular")
@requiere_rol("administrador", "trabajador")
def calcular():
    data = request.get_json(force=True) or {}
    resultado, error = _calcular_o_error(data)
    if error:
        return error
    return jsonify(resultado)


@escalera_bp.post("/pdf")
@requiere_rol("administrador", "trabajador")
def pdf():
    data = request.get_json(force=True) or {}
    # Se recalcula en el servidor con los mismos datos — nunca se confía en
    # números que vengan ya calculados del cliente.
    resultado, error = _calcular_o_error(data)
    if error:
        return error

    from ficha_pdf import generar_ficha_pdf
    imagen_3d_base64 = data.get("imagen_3d_base64")
    buffer = generar_ficha_pdf(resultado, ETIQUETAS, NOMBRE_TIPO, imagen_3d_base64=imagen_3d_base64)

    from flask import send_file
    nombre_archivo = f"escalera-{resultado['tipo']}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=nombre_archivo)


@escalera_bp.post("/excel")
@requiere_rol("administrador", "trabajador")
def excel():
    data = request.get_json(force=True) or {}
    resultado, error = _calcular_o_error(data)
    if error:
        return error

    from ficha_excel import generar_ficha_excel
    buffer = generar_ficha_excel(resultado, ETIQUETAS, NOMBRE_TIPO)

    from flask import send_file
    nombre_archivo = f"escalera-{resultado['tipo']}.xlsx"
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre_archivo,
    )
