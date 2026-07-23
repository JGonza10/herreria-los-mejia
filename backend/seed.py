"""
Llena la base de datos con precios base, catálogo de ejemplo y usuarios de
prueba (uno por cada rol). Ejecutar una sola vez: python seed.py

IMPORTANTE: cambia las contraseñas de ejemplo antes de usar el sitio con
clientes reales — puedes hacerlo desde el panel de administrador o
directamente en la base de datos.
"""
from app import create_app
from extensions import db
from models import PrecioMaterial, Producto, Usuario

app = create_app()

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

with app.app_context():
    db.create_all()

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
        {"nombre": "Admin Los Mejía", "email": "admin@losmejia.com", "password": "cambiar123", "rol": "administrador"},
        {"nombre": "Trabajador Ejemplo", "email": "trabajador@losmejia.com", "password": "cambiar123", "rol": "trabajador"},
        {"nombre": "Cliente Ejemplo", "email": "cliente@losmejia.com", "password": "cambiar123", "rol": "cliente"},
    ]
    for datos in USUARIOS_EJEMPLO:
        if not Usuario.query.filter_by(email=datos["email"]).first():
            usuario = Usuario(nombre=datos["nombre"], email=datos["email"], rol=datos["rol"])
            usuario.set_password(datos["password"])
            db.session.add(usuario)

    db.session.commit()
    print("Datos de ejemplo cargados correctamente.")
    print("Usuarios de prueba (cambia las contraseñas antes de producción):")
    for datos in USUARIOS_EJEMPLO:
        print(f"  {datos['rol']}: {datos['email']} / {datos['password']}")
