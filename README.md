# Herrería Los Mejía

Sistema web de cotización y gestión para un taller de herrería, aluminio y vidrio, con paneles separados para administrador, trabajador y cliente.

## Estado actual

**En desarrollo activo, con una versión desplegada en producción** en Railway (`https://herreria-los-mejia-production.up.railway.app/`).

No existe una suite de pruebas end-to-end automatizada sobre el sitio real: la validación de cada entrega se hace con un checklist de pruebas manuales, documentado en [`ESTADO_Y_PRUEBAS.md`](./ESTADO_Y_PRUEBAS.md) (última actualización: 31 de julio de 2026), que a esa fecha aún tenía casillas por marcar. Sí hay pruebas automatizadas de backend con `pytest` (`backend/tests/`) que corren en CI (GitHub Actions) en cada push a `main`, junto con el build de producción del frontend. En resumen: es un producto usable y en uso real, pero todavía en construcción — el plan de trabajo (`actualizar.md`) tiene fases abiertas.

## Características principales

- **Sistema de tres roles** (administrador, trabajador, cliente), cada uno con su panel y permisos propios, protegidos con el decorador `@requiere_rol` del backend.
- **Cotizador público** basado en una especificación unificada de pieza (`spec`), de la que salen el dibujo, el precio y la lista de corte:
  - Catálogo de 9 tipos de trabajo: portón corredizo, portón abatible, reja, protección, barandal, cancelería, ventana de aluminio, puerta de cristal templado y escalera.
  - Permite agregar varias piezas en una sola solicitud; el precio siempre se muestra como rango (±10 %), nunca como número exacto.
  - Tarifas de precios versionadas, editables desde el panel de administrador sin tocar código.
  - Simulador de cotización para el administrador (mano de obra, flete, merma, utilidad, IVA) que no afecta lo ya guardado.
- **Vista previa en 2D y 3D** de las piezas mientras se capturan las medidas (three.js), incluida una calculadora de escaleras con validaciones basadas en el Reglamento de Construcciones de CDMX y la Ley de Blondel.
- **Chatbot de atención** integrado con la API de Anthropic (Claude), limitado a 20 peticiones por hora por IP.
- **Operación de taller**: lista de corte con merma real por partida, orden de trabajo en PDF sin precios, requisición de material consolidada entre proyectos activos, agenda de capacidad semanal.
- **Seguimiento de proyectos**: aceptación pública de cotización por link (sin cuenta), registro de anticipos y pagos, fotos de avance subidas por el trabajador y visibles para el cliente, cotizaciones vencidas que se marcan solas y pueden revivirse con la tarifa vigente.
- **Bitácora de auditoría** de cambios de precio, estado y asignación.
- **Reportes de negocio**: costo real contra cotizado, tasa de conversión por tipo de trabajo y rango de precio, horas por m², exportables a Excel.

## Stack tecnológico

**Backend**
- Python 3 + Flask 3, Flask-SQLAlchemy
- PostgreSQL en producción, con caída automática a SQLite si no hay `DATABASE_URL` (desarrollo local)
- Flask-Migrate (Alembic) para migraciones de esquema
- Flask-Limiter (límite de peticiones al chatbot) y Flask-Cors
- Autenticación por token firmado con `itsdangerous` en el header `Authorization: Bearer` (no por cookie, por diseño: frontend y backend viven en dominios distintos de Railway)
- `reportlab` (PDF) y `XlsxWriter` (Excel)
- Integración con la **API de Anthropic (Claude)** para el chatbot
- `pytest` para pruebas automatizadas

**Frontend**
- React 18 + Vite + React Router
- three.js para las vistas 2D/3D de piezas y escaleras

**Despliegue**
- Dos servicios independientes en Railway (backend y frontend), con PostgreSQL administrado por Railway
- CI en GitHub Actions: pytest del backend y build de Vite del frontend en cada push/PR a `main`

## Estructura del proyecto

```
06 herreria-los-mejia/
├── backend/
│   ├── app.py           # fábrica de la app Flask, registro de blueprints
│   ├── models.py        # modelos SQLAlchemy
│   ├── auth.py           # tokens firmados y decorador @requiere_rol
│   ├── dominio/           # especificación unificada de pieza (spec), precios, geometría, despiece
│   ├── routes/            # un blueprint por área (auth, catalogo, cotizador, chatbot,
│   │                       admin, trabajador, cliente, escalera, tarifas)
│   ├── tests/             # pruebas automatizadas con pytest
│   ├── migrations/        # migraciones Alembic
│   └── seed.py, respaldar_db.py, vencer_cotizaciones.py, migrar_*.py  # scripts de mantenimiento
├── frontend/
│   └── src/
│       ├── pages/          # sitio público, login, registro, paneles por rol (incluye admin/)
│       ├── components/      # cotizador, vistas 2D/3D, chatbot, layout
│       └── context/          # tema claro/oscuro, autenticación
├── CLAUDE.md              # contexto y convenciones del proyecto
├── ESTADO_Y_PRUEBAS.md    # qué incluye la versión actual y checklist de pruebas manuales
└── actualizar.md           # plan de mejoras por fases
```

> **Sobre `herreria-v2/`:** es una carpeta presente en el directorio local pero **excluida del repositorio** (está en `.gitignore`). Corresponde a una versión anterior y más simple —sesión por cookie en vez de token firmado, sin Flask-Migrate ni Flask-Limiter, `SECRET_KEY` con valor por defecto inseguro— sin ninguna de las fases más recientes del plan (tarifas versionadas, requisición, agenda, reportes, bitácora). **La versión vigente es la de la raíz** (`backend/` y `frontend/`); `herreria-v2/` no debe usarse como referencia ni desplegarse.

## Cómo instalar y ejecutar en local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Editar .env con los valores propios (ver variables abajo)

python seed.py                  # carga catálogo, tarifas y usuarios de prueba
python app.py                   # http://localhost:5000
```

Sin `DATABASE_URL` definida, el backend usa SQLite automáticamente (`sqlite:///local.db`); no hace falta PostgreSQL instalado para desarrollar en local.

Variables de entorno relevantes (`backend/.env`, nunca se sube al repositorio):

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Firma los tokens de sesión. Obligatoria en producción; si falta ahí, la app no arranca. |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL. Si se omite, se usa SQLite local. |
| `ANTHROPIC_API_KEY` | Llave de la API de Anthropic para el chatbot. Sin ella, el endpoint responde un error controlado. |
| `FRONTEND_ORIGIN` | Origen permitido por CORS. |
| `PORT` | Puerto del servidor Flask. |
| `SEED_ADMIN_PASSWORD`, `SEED_TRABAJADOR_PASSWORD`, `SEED_CLIENTE_PASSWORD` | Contraseñas de las cuentas de prueba que crea `seed.py` (mínimo 12 caracteres); el script no corre si faltan. |

Pruebas de backend:

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## Documentación relacionada

- [`ESTADO_Y_PRUEBAS.md`](./ESTADO_Y_PRUEBAS.md) — qué incluye la versión actual, fase por fase, y el checklist de pruebas manuales para validar el sitio antes de dar por buena una entrega. Es la referencia más confiable sobre qué tan probado está cada módulo hoy.
- [`CLAUDE.md`](./CLAUDE.md) — contexto permanente del proyecto, convenciones de código, decisiones de arquitectura ya tomadas y trampas conocidas del repositorio. Punto de partida obligado antes de proponer cambios estructurales.
- [`actualizar.md`](./actualizar.md) — plan de mejoras por fases, en orden de dependencia.

## Notas relevantes

- **Todo el código está en español** (variables, funciones, rutas, tablas, mensajes de error) de forma deliberada; es la convención del proyecto.
- La `ANTHROPIC_API_KEY` se lee desde variable de entorno en `backend/routes/chatbot.py` y no aparece hardcodeada en el código revisado. Aun así, conviene confirmar que ninguna llave real haya quedado commiteada por error en el historial de git, y rotarla de inmediato si eso ocurriera.
- El disco de Railway es efímero: las imágenes del catálogo en `backend/uploads/` se pierden en cada despliegue salvo que se configure un Volume montado en esa ruta.
- Los tokens de sesión no tienen lista negra y duran 30 días; la única forma de revocarlos es cambiar `SECRET_KEY` (invalida todas las sesiones) o el `token_version` del usuario (invalida solo las suyas).
- No hay recuperación de contraseña por correo: es una decisión deliberada dado el tamaño del negocio; el administrador restablece contraseñas desde el panel de Equipo.
- Antes de cualquier migración contra datos reales, respaldar con `pg_dump` o `backend/respaldar_db.py`, y probar primero en un ambiente de staging.
