"""
Agrega a la tarifa activa los precios de aluminio (perfil ml + cristal m2) y
cristal templado (material_base m2 + canteado ml) que faltaban desde
seed_tarifa_inicial.py — sin esos dos sistemas no se podían cotizar con el
endpoint de partidas (ver dominio/precios.py, cotizar_partida).

Son precios de REFERENCIA de mercado en CDMX (investigados, no son la
lista real del proveedor del taller):
    perfil/aluminio       $600/ml   (serie 3500 gama media, armado)
    cristal/vidrio        $1,200/m2 (vidrio claro sin templar)
    material_base/cristal_templado  $1,800/m2
    canteado/cristal_templado       $100/ml
El dueño debe ajustarlos en Admin → Tarifas en cuanto tenga su lista real.

Uso:
    python agregar_precios_aluminio_templado.py
Seguro de correr más de una vez: no duplica un (concepto, clave) que ya
exista en la tarifa activa, solo actualiza su precio.
"""
from models import Tarifa, PrecioTarifa
from app import create_app
from extensions import db

app = create_app()

PRECIOS_NUEVOS = [
    {"concepto": "perfil", "clave": "aluminio", "unidad": "ml", "precio": 600},
    {"concepto": "cristal", "clave": "vidrio", "unidad": "m2", "precio": 1200},
    {"concepto": "material_base", "clave": "cristal_templado", "unidad": "m2", "precio": 1800},
    {"concepto": "canteado", "clave": "cristal_templado", "unidad": "ml", "precio": 100},
]

with app.app_context():
    tarifa = Tarifa.query.filter_by(activa=True).first()
    if not tarifa:
        raise SystemExit("No hay ninguna tarifa activa. Corre seed_tarifa_inicial.py primero.")

    agregados, actualizados = 0, 0
    for datos in PRECIOS_NUEVOS:
        fila = PrecioTarifa.query.filter_by(
            tarifa_id=tarifa.id, concepto=datos["concepto"], clave=datos["clave"],
        ).first()
        if fila:
            fila.precio = datos["precio"]
            actualizados += 1
        else:
            db.session.add(PrecioTarifa(tarifa_id=tarifa.id, **datos))
            agregados += 1

    db.session.commit()
    print(f"Tarifa '{tarifa.nombre}' (id={tarifa.id}): {agregados} precio(s) agregado(s), {actualizados} actualizado(s).")
    print()
    print("Precios de referencia de mercado (CDMX) — ajustar cuando haya lista real del proveedor.")
