"""
Backfill de la Fase 2 (actualizar.md): las cotizaciones creadas antes de que
existiera la columna `spec` no la tienen. Este script la construye a partir
de material/ancho_m/alto_m/con_acabado — los mismos datos que ya guardaba
cada cotización — y las marca con tipo "indefinido", porque el catálogo
todavía no liga cada producto a un TipoTrabajo (eso llega en la Fase 4).

Ejecutar una sola vez, después de correr `flask db upgrade`:
    python migrar_specs.py
Es seguro correrlo más de una vez: solo toca las filas con spec nulo.
"""
from app import create_app
from extensions import db
from models import Cotizacion
from dominio.spec import construir_basico

app = create_app()

with app.app_context():
    pendientes = Cotizacion.query.filter(Cotizacion.spec.is_(None)).all()
    for cotizacion in pendientes:
        cotizacion.spec = construir_basico(
            cotizacion.material,
            float(cotizacion.ancho_m),
            float(cotizacion.alto_m),
            cotizacion.con_acabado,
            tipo="indefinido",
        )
    db.session.commit()
    print(f"{len(pendientes)} cotización(es) actualizada(s) con spec.")
