"""Especificación unificada de pieza: la estructura de datos que describe
qué se va a fabricar, de la que salen el dibujo (2D/3D), el precio y el
despiece (ver actualizar.md, Fase 2). Funciones puras — sin Flask, sin
SQLAlchemy — para que se puedan usar desde una ruta, un script o una prueba
sin cargar el resto de la aplicación.

El campo 'version' existe desde el día uno: cuando esta forma cambie —y va
a cambiar, según el propio plan— las cotizaciones viejas necesitan poder
seguir dibujándose con la forma que tenían cuando se crearon.
"""
from models import SISTEMAS

VERSION_ACTUAL = 1

SISTEMA_POR_MATERIAL = {
    "hierro": "herreria",
    "aluminio": "aluminio",
    "vidrio": "cristal_templado",
}


def construir_basico(material, ancho_m, alto_m, con_acabado, tipo="indefinido", sistema=None):
    """Arma el spec más simple posible a partir de lo que hoy captura el
    cotizador (material + medidas). Los campos que todavía no se preguntan
    (perfil, herrajes, separación de barrotes...) quedan vacíos hasta que
    exista un formulario que los capture — no se inventan valores."""
    return {
        "version": VERSION_ACTUAL,
        "tipo": tipo,
        "sistema": sistema or SISTEMA_POR_MATERIAL.get(material, "herreria"),
        "medidas": {"ancho_m": round(float(ancho_m), 2), "alto_m": round(float(alto_m), 2)},
        "piezas": 1,
        "estructura": {},
        "relleno": {},
        "acabado": "con_acabado" if con_acabado else "estandar",
        "herrajes": [],
        "notas": None,
    }


def validar(spec):
    """Lanza ValueError con mensaje legible si el spec no es válido. No
    devuelve nada — se usa antes de guardar o cotizar."""
    if not isinstance(spec, dict):
        raise ValueError("El spec debe ser un objeto.")
    if not isinstance(spec.get("version"), int):
        raise ValueError("Falta 'version' (entero) en el spec.")
    if not spec.get("tipo"):
        raise ValueError("Falta 'tipo' en el spec.")
    if spec.get("sistema") not in SISTEMAS:
        raise ValueError(f"'sistema' debe ser uno de: {', '.join(SISTEMAS)}.")

    medidas = spec.get("medidas") or {}
    for campo in ("ancho_m", "alto_m"):
        valor = medidas.get(campo)
        if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor <= 0:
            raise ValueError(f"'medidas.{campo}' debe ser un número mayor a 0.")

    piezas = spec.get("piezas", 1)
    if not isinstance(piezas, int) or isinstance(piezas, bool) or piezas < 1:
        raise ValueError("'piezas' debe ser un entero mayor o igual a 1.")

    for herraje in spec.get("herrajes") or []:
        if not isinstance(herraje, dict) or "clave" not in herraje or "cantidad" not in herraje:
            raise ValueError("Cada herraje debe tener 'clave' y 'cantidad'.")
