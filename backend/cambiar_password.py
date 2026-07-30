"""
Cambia la contraseña de un usuario ya existente en la base de datos, sin
pasar por el panel de administrador. Útil para fijar las contraseñas reales
en producción después de correr seed.py, o para restablecer la de alguien
que la olvidó.

Uso:
    python cambiar_password.py admin@losmejia.com

Pide la contraseña nueva por consola (no se imprime en pantalla ni queda en
el historial de la shell) y la confirma dos veces antes de guardarla.
"""
import argparse
import getpass
import sys

from app import create_app
from extensions import db
from models import Usuario

LONGITUD_MINIMA = 12


def pedir_password_nueva():
    while True:
        password = getpass.getpass("Contraseña nueva: ")
        if len(password) < LONGITUD_MINIMA:
            print(f"Debe tener al menos {LONGITUD_MINIMA} caracteres.")
            continue
        confirmacion = getpass.getpass("Confírmala: ")
        if password != confirmacion:
            print("No coinciden, intenta de nuevo.")
            continue
        return password


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email", help="Correo del usuario cuya contraseña se va a cambiar")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        usuario = Usuario.query.filter_by(email=args.email).first()
        if not usuario:
            sys.exit(f"No existe ningún usuario con el correo '{args.email}'.")

        print(f"Usuario: {usuario.nombre} ({usuario.rol})")
        password = pedir_password_nueva()
        usuario.set_password(password)
        usuario.token_version += 1  # invalida cualquier token de sesión que ya tuviera
        db.session.commit()
        print(f"Contraseña actualizada para {args.email}.")


if __name__ == "__main__":
    main()
