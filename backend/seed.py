"""
Llena la base de datos con precios base, catálogo de ejemplo y usuarios de
prueba (uno por cada rol). Ejecutar una sola vez: python seed.py

Requiere que el esquema ya exista (corre `flask db upgrade` antes) — este
script ya no crea tablas, solo datos.

Las contraseñas de los usuarios de prueba se toman de variables de entorno
(SEED_ADMIN_PASSWORD, SEED_TRABAJADOR_PASSWORD, SEED_CLIENTE_PASSWORD) — el
script no corre si faltan, para que nunca queden contraseñas fijas en el
código ni en el repositorio.
"""
import os
import sys

from app import create_app
from extensions import db
from models import PrecioMaterial, Producto, TipoTrabajo, Usuario

app = create_app()


def password_requerido(nombre_var):
    valor = os.environ.get(nombre_var)
    if not valor or len(valor) < 12:
        sys.exit(f"Falta {nombre_var} (mínimo 12 caracteres). El seed no corre sin ella.")
    return valor


PASSWORD_ADMIN = password_requerido("SEED_ADMIN_PASSWORD")
PASSWORD_TRABAJADOR = password_requerido("SEED_TRABAJADOR_PASSWORD")
PASSWORD_CLIENTE = password_requerido("SEED_CLIENTE_PASSWORD")

PRECIOS = [
    {"material": "hierro", "precio_base_m2": 1200, "precio_acabado_extra_m2": 250},
    {"material": "aluminio", "precio_base_m2": 1450, "precio_acabado_extra_m2": 300},
    {"material": "vidrio", "precio_base_m2": 1800, "precio_acabado_extra_m2": 400},
]

PRODUCTOS = [
    {
        "nombre": "Portón corredizo clásico",
        "material": "hierro",
        "descripcion": "Portón de hierro forjado con diseño de barrotes, ideal para cocheras y entradas principales.",
        "precio_referencia_m2": 1200,
        "destacado": True,
    },
    {
        "nombre": "Reja de protección ornamental",
        "material": "hierro",
        "descripcion": "Reja decorativa para ventanas con motivos forjados a mano.",
        "precio_referencia_m2": 1100,
        "destacado": False,
    },
    {
        "nombre": "Barandal de escalera moderno",
        "material": "aluminio",
        "descripcion": "Barandal ligero y resistente a la corrosión, acabado en pintura electrostática.",
        "precio_referencia_m2": 1450,
        "destacado": True,
    },
    {
        "nombre": "Cancelería de aluminio para balcón",
        "material": "aluminio",
        "descripcion": "Estructura de aluminio para balcones y terrazas, bajo mantenimiento.",
        "precio_referencia_m2": 1400,
        "destacado": False,
    },
    {
        "nombre": "Ventana fija con vidrio templado",
        "material": "vidrio",
        "descripcion": "Ventana fija con vidrio templado de seguridad, ideal para fachadas.",
        "precio_referencia_m2": 1800,
        "destacado": True,
    },
    {
        "nombre": "División de baño en vidrio esmerilado",
        "material": "vidrio",
        "descripcion": "División interior con vidrio esmerilado para privacidad y luz natural.",
        "precio_referencia_m2": 1750,
        "destacado": False,
    },
]

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
    for t in TIPOS_TRABAJO:
        if not TipoTrabajo.query.filter_by(clave=t["clave"]).first():
            db.session.add(TipoTrabajo(**t))

    for p in PRECIOS:
        existente = PrecioMaterial.query.filter_by(material=p["material"]).first()
        if existente:
            existente.precio_base_m2 = p["precio_base_m2"]
            existente.precio_acabado_extra_m2 = p["precio_acabado_extra_m2"]
        else:
            db.session.add(PrecioMaterial(**p))

    if Producto.query.count() == 0:
        for prod in PRODUCTOS:
            db.session.add(Producto(**prod))

    USUARIOS_EJEMPLO = [
        {"nombre": "Admin Los Mejía", "email": "admin@losmejia.com", "password": PASSWORD_ADMIN, "rol": "administrador"},
        {"nombre": "Trabajador Ejemplo", "email": "trabajador@losmejia.com", "password": PASSWORD_TRABAJADOR, "rol": "trabajador"},
        {"nombre": "Cliente Ejemplo", "email": "cliente@losmejia.com", "password": PASSWORD_CLIENTE, "rol": "cliente"},
    ]
    for datos in USUARIOS_EJEMPLO:
        if not Usuario.query.filter_by(email=datos["email"]).first():
            usuario = Usuario(nombre=datos["nombre"], email=datos["email"], rol=datos["rol"])
            usuario.set_password(datos["password"])
            db.session.add(usuario)

    db.session.commit()
    print("Datos de ejemplo cargados correctamente.")
    print("Usuarios de prueba (contraseñas tomadas de las variables de entorno, no se imprimen):")
    for datos in USUARIOS_EJEMPLO:
        print(f"  {datos['rol']}: {datos['email']}")
