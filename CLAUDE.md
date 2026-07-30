# CLAUDE.md

Contexto permanente del proyecto. Se lee al inicio de cada sesión.

## Qué es esto

Sitio y sistema de gestión para **Herrería Los Mejía**, un taller que trabaja hierro,
aluminio y vidrio: portones, rejas, barandales, ventanas, cancelería y escaleras.

El sistema tiene tres roles (cliente, trabajador, administrador), catálogo de productos,
cotizador, seguimiento de proyectos, un chatbot de atención y una calculadora de escaleras
con visualización 3D.

**El objetivo del negocio**, y el criterio para priorizar cualquier decisión: que el dueño
del taller pueda tomar las medidas que da un cliente, simular la cotización, ver la pieza
en 2D y 3D, e **imprimirla para mostrársela al cliente**.

## Stack

- **Backend:** Flask 3 + Flask-SQLAlchemy + PostgreSQL · `backend/`
- **Frontend:** React 18 + Vite + React Router + three.js 0.160 · `frontend/`
- **Despliegue:** dos servicios separados en Railway (backend y frontend), con PostgreSQL
- **PDF y Excel:** reportlab y XlsxWriter, en el backend

## Correr en local

```bash
# Backend — sin DATABASE_URL cae a SQLite, no hace falta PostgreSQL local
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py                   # http://localhost:5000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

`backend/.env` (nunca se sube, está en `.gitignore`):
`SECRET_KEY`, `ANTHROPIC_API_KEY`, `FRONTEND_ORIGIN`, `PORT`. Sin `DATABASE_URL` para usar SQLite.

## Convenciones del código

- **Todo en español**: nombres de variables, funciones, rutas, tablas, comentarios y
  mensajes de error. `calcular_precio`, `requiere_rol`, `precio_base_m2`. Mantenerlo así.
- Un blueprint por área en `backend/routes/`, registrado en `app.py` con prefijo `/api/`.
- Los modelos exponen `to_dict()` para serializar. Seguir ese patrón en modelos nuevos.
- Autenticación por token firmado con `itsdangerous` en el header `Authorization: Bearer`,
  no por cookie. Fue una decisión deliberada: el frontend y el backend viven en dominios
  distintos de Railway y los navegadores bloquean las cookies cross-site. **No cambiar a
  cookies sin resolver eso primero.**
- El decorador `@requiere_rol("administrador")` de `backend/auth.py` protege las rutas.
- Medidas **siempre en metros** en todo el sistema. La única excepción permitida es la
  separación entre barrotes, en centímetros, porque así la dice el herrero.

## Trampas conocidas de este repo

Cosas que ya costaron trabajo descubrir. No revertirlas sin entender por qué están.

1. **`app.py` fuerza el driver `postgresql+psycopg://`.** `psycopg2-binary` falla en el
   builder de Railway con `libpq.so.5 no encontrado`. El reemplazo de la cadena de
   conexión es a propósito.
2. **No hay migraciones todavía.** `app.py` corre `db.create_all()`, que crea tablas
   nuevas pero **nunca modifica** las existentes. Agregar una columna sin Alembic significa
   que producción se queda atrás en silencio. Meter Flask-Migrate es la Fase 1.1 y es
   requisito para casi todo lo demás.
3. **El disco de Railway es efímero.** Las imágenes del catálogo en `backend/uploads/`
   se borran en cada deploy salvo que haya un Volume montado.
4. **Los tokens de sesión no se pueden revocar.** Son sin estado y duran 30 días.
   `logout` solo los borra del navegador.
5. **`SECRET_KEY` firma los tokens.** Si cambia, todas las sesiones abiertas se caen.
   Es aceptable y a veces deseable, pero hay que saberlo antes de cambiarla.
6. **El endpoint del chatbot reenvía a una API de paga** con la llave del taller.
   Cualquier cambio ahí tiene consecuencias de dinero, no solo de código.

## El plan de trabajo

Está en **`actualizar.md`**, en la raíz. Ocho fases en orden de dependencia.
Leerlo antes de proponer cambios estructurales.

Estado actual: **Fase 0** (seguridad urgente y limpieza).

La Fase 2 —la especificación unificada de pieza— es la que desbloquea las fases 3, 5 y 6.
Si algo de lo que se va a hacer se puede posponer hasta después de la Fase 2, posponerlo.

## Cómo trabajar aquí

- **`main` es exactamente lo que está desplegado.** No se le hace commit directo.
- Una rama corta por tarea: `fase-0/seguridad`, `fase-1/alembic`. Días, no semanas.
  **No** crear una rama `v2` de larga vida: se desincroniza y nunca se fusiona.
- Cambios chicos y revisables. Antes de un refactor grande, primero las pruebas que
  fijan el comportamiento actual, y después el refactor.
- **Nunca** commitear `.env`, llaves de API ni contraseñas. Si algo así aparece en un
  diff, detenerse y avisar.
- Antes de cualquier migración contra datos reales: respaldo con `pg_dump` y prueba en
  el ambiente de staging de Railway.
- Preguntar antes de: cambiar el esquema de la base, tocar el flujo de autenticación,
  o modificar cómo se calculan los precios. Son las tres áreas donde un error se
  convierte en dinero perdido o en datos corruptos.

## Lo que no hay que construir

Decidido y cerrado. Si parece buena idea, ya se discutió y la respuesta fue no:

- Reescribir a Next.js o TypeScript, o cambiar de framework.
- Un CAD, o importar DXF de arquitectos. El modelo paramétrico cubre lo que fabrica el taller.
- Microservicios, Docker Compose elaborado, Kubernetes.
- App móvil nativa. Si hace falta, PWA.
- La API de WhatsApp Business. Links `wa.me` dan casi todo el beneficio por cero pesos.
- Pasarela de pagos en línea. Los anticipos se pagan por transferencia; falta registrarlos,
  no cobrarlos.
- Convertirlo en SaaS para otras herrerías.
- IA generativa para diseñar piezas.

## Contexto humano

Lo desarrolla el dueño del proyecto junto con su hijo. Los usuarios finales son el dueño
de una herrería y sus trabajadores, que van a usar esto desde el teléfono, en el taller y
en obra, a veces con mala señal. Peso de página y claridad de la interfaz importan más
que la elegancia técnica.
