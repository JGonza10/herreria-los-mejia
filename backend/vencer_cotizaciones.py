"""
Marca como 'vencida' cualquier cotización cuya vigencia_hasta ya pasó y que
no ha sido aceptada ni rechazada (Fase 7.4). Pensado para correr una vez al
día como Cron Job de Railway (o cualquier cron):
    python vencer_cotizaciones.py

Una cotización de hace 4 meses con precios de hace 4 meses es una pérdida
garantizada — revívela con POST /api/admin/cotizaciones/<id>/revivir antes
de volver a mandarla, en vez de reenviar el precio viejo.
"""
from datetime import date

from app import create_app
from extensions import db
from models import Cotizacion

app = create_app()

with app.app_context():
    vencidas = Cotizacion.query.filter(
        Cotizacion.vigencia_hasta.isnot(None),
        Cotizacion.vigencia_hasta < date.today(),
        Cotizacion.aceptada_en.is_(None),
        Cotizacion.estado.notin_(("rechazada", "vencida")),
    ).all()
    for cotizacion in vencidas:
        cotizacion.estado = "vencida"
    db.session.commit()
    print(f"{len(vencidas)} cotización(es) marcada(s) como vencida(s).")
