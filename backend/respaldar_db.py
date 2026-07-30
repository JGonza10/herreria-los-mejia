"""
Respaldo manual de la base de datos de producción. Usar mientras no esté
confirmado si el plan de Railway incluye respaldos automáticos de Postgres.

Uso (con la DATABASE_URL real de producción, no la pegues en ningún chat):
    DATABASE_URL="postgresql://..." python respaldar_db.py

Genera un archivo `respaldo-AAAAMMDD-HHMMSS.sql` en el directorio actual.
Requiere tener `pg_dump` instalado (viene con el cliente de PostgreSQL).
"""
import os
import subprocess
import sys
from datetime import datetime


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("Falta DATABASE_URL.")
    if database_url.startswith("sqlite"):
        sys.exit("DATABASE_URL apunta a SQLite: no hay nada que respaldar con pg_dump.")

    nombre_archivo = f"respaldo-{datetime.now():%Y%m%d-%H%M%S}.sql"
    print(f"Respaldando a {nombre_archivo}...")
    with open(nombre_archivo, "wb") as archivo:
        resultado = subprocess.run(["pg_dump", database_url], stdout=archivo)

    if resultado.returncode != 0:
        os.remove(nombre_archivo)
        sys.exit("pg_dump falló — revisa que esté instalado (cliente de PostgreSQL) y que la URL sea correcta.")

    print("Listo.")


if __name__ == "__main__":
    main()
