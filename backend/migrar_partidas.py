"""
Backfill de la Fase 4.1 (actualizar.md): las cotizaciones creadas antes de
que existiera Partida son "una sola pieza" — este script convierte cada una
en una cotización con una sola partida, usando los mismos datos que ya
tenía guardados (material/ancho_m/alto_m/precio_estimado/spec). También les
pone folio y vigencia_hasta si no los tienen.

No recalcula precios ni cambia el precio_estimado ya guardado: usa el que
la cotización ya tenía, para que el número que el cliente ya vio no cambie.

Ejecutar una sola vez, después de correr `flask db upgrade` y `migrar_specs.py`:
    python migrar_partidas.py
Es seguro correrlo más de una vez: solo toca cotizaciones sin partidas.
"""
from datetime import timedelta

from app import create_app
from extensions import db
from models import Cotizacion, Partida

app = create_app()

VIGENCIA_DIAS = 30

with app.app_context():
    pendientes = Cotizacion.query.filter(~Cotizacion.partidas.any()).all()
    for cotizacion in pendientes:
        spec = cotizacion.spec or {
            "version": 1, "tipo": "indefinido", "sistema": "herreria",
            "medidas": {"ancho_m": float(cotizacion.ancho_m), "alto_m": float(cotizacion.alto_m)},
            "piezas": 1, "estructura": {}, "relleno": {}, "herrajes": [],
            "acabado": "con_acabado" if cotizacion.con_acabado else "estandar", "notas": None,
        }
        partida = Partida(
            cotizacion_id=cotizacion.id,
            spec=spec,
            descripcion=spec.get("tipo", "indefinido"),
            cantidad=cotizacion.metros_cuadrados,
            precio_unitario=cotizacion.precio_estimado,
            importe=cotizacion.precio_estimado,
            orden=0,
        )
        db.session.add(partida)

        if cotizacion.subtotal is None:
            cotizacion.subtotal = cotizacion.precio_estimado
        if cotizacion.total is None:
            cotizacion.total = cotizacion.precio_estimado
        if cotizacion.vigencia_hasta is None:
            cotizacion.vigencia_hasta = cotizacion.creado_en.date() + timedelta(days=VIGENCIA_DIAS)
        if cotizacion.folio is None:
            cotizacion.folio = f"LM-{cotizacion.creado_en.year}-{cotizacion.id:04d}"

    db.session.commit()
    print(f"{len(pendientes)} cotización(es) migrada(s) a partidas.")
