"""Validación de datos de entrada, sin depender de Flask."""


def numero(valor, campo, minimo=0, maximo=None):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"'{campo}' debe ser un número.")
    if n < minimo or (maximo is not None and n > maximo):
        raise ValueError(f"'{campo}' fuera de rango.")
    return n
