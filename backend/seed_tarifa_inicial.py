"""
Siembra el catálogo de tipos de trabajo (Fase 2) y una primera Tarifa
(Fase 4.2) para producción — sin tocar PrecioMaterial, Producto ni los
usuarios, que ya viven en producción con datos reales.

Los precios de la tarifa para herrería se copian de PrecioMaterial (los
mismos que ya usa el cotizador de una sola pieza), para que ambos caminos
den el mismo número mientras no se capturen precios distintos a propósito.

Los precios de aluminio (perfil ml + cristal m2) y cristal templado
(material_base m2 + canteado ml) NO se inventan aquí — no existe un dato
real del que copiarlos. El script los deja fuera y avisa al final; hay que
cargarlos a mano en Admin → Tarifas (PUT /api/admin/tarifas/<id>/precios)
antes de cotizar una pieza de esos dos sistemas con el endpoint nuevo.

Uso:
    python seed_tarifa_inicial.py
Seguro de correr más de una vez: no duplica tipos de trabajo ni tarifas.
"""
from datetime import date

from app import create_app
from extensions import db
from models import PrecioMaterial, Tarifa, PrecioTarifa, TipoTrabajo

app = create_app()

TIPOS_TRABAJO = [
    {"clave": "porton_corredizo", "nombre": "Portón corredizo", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "porton_abatible", "nombre": "Portón abatible", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "reja_cerca", "nombre": "Reja o cerca", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "proteccion_ventana", "nombre": "Protección para ventana", "sistema": "herreria", "unidad": "m2", "modo_dibujo": "barrotes"},
    {"clave": "barandal", "nombre": "Barandal", "sistema": "herreria", "unidad": "ml", "altura_referencia_m": 1.00, "modo_dibujo": "estructura"},
    {"clave": "canceleria", "nombre": "Cancelería", "sistema": "aluminio", "unidad": "m2", "modo_dibujo": "cancel", "admite_barrotes": False},
    {"clave": "ventana_aluminio", "nombre": "Ventana de aluminio", "sistema": "aluminio", "unidad": "m2", "modo_dibujo": "cancel", "admite_barrotes": False},
    {"clave": "puerta_cristal_templado", "nombre": "Puerta de cristal templado", "sistema": "cristal_templado", "unidad": "m2", "modo_dibujo": "vidrio", "admite_barrotes": False},
    {"clave": "escalera", "nombre": "Escalera", "sistema": "herreria", "unidad": "ml", "modo_dibujo": "estructura", "admite_barrotes": False},
]

with app.app_context():
    creados_tipos = 0
    for t in TIPOS_TRABAJO:
        if not TipoTrabajo.query.filter_by(clave=t["clave"]).first():
            db.session.add(TipoTrabajo(**t))
            creados_tipos += 1

    tarifa = Tarifa.query.filter_by(activa=True).first()
    creo_tarifa = False
    if not tarifa:
        tarifa = Tarifa(nombre=f"Inicial {date.today():%B %Y}", vigente_desde=date.today(), activa=True)
        db.session.add(tarifa)
        db.session.flush()
        creo_tarifa = True

        for material in PrecioMaterial.query.all():
            db.session.add(PrecioTarifa(
                tarifa_id=tarifa.id, concepto="material_base", clave=material.material,
                unidad="m2", precio=material.precio_base_m2,
            ))
            db.session.add(PrecioTarifa(
                tarifa_id=tarifa.id, concepto="acabado", clave=material.material,
                unidad="m2", precio=material.precio_acabado_extra_m2,
            ))

    db.session.commit()

    print(f"{creados_tipos} tipo(s) de trabajo nuevo(s).")
    if creo_tarifa:
        print(f"Tarifa '{tarifa.nombre}' creada y activada (id={tarifa.id}), con precios de herrería copiados de PrecioMaterial.")
        print()
        print("AVISO: falta cargar precios de 'perfil'/aluminio, 'cristal'/vidrio,")
        print("'material_base'/cristal_templado y 'canteado'/cristal_templado antes de")
        print("poder cotizar aluminio o cristal templado con el endpoint de partidas —")
        print("no existe un precio real del que copiarlos todavía.")
    else:
        print(f"Ya había una tarifa activa (id={tarifa.id}, '{tarifa.nombre}'); no se creó otra.")
