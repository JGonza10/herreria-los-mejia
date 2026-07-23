# Herrería Los Mejía — Sitio web con sistema de roles

Sitio web para la herrería "Los Mejía" (hierro, aluminio y vidrio):
catálogo con imágenes, cotizador por m², seguimiento de pedidos, chatbot
con IA, y un sistema de 3 roles (administrador, trabajador, cliente).

## Stack
- **Backend:** Flask + SQLAlchemy + PostgreSQL, sesiones de login con cookie
- **Frontend:** React + Vite + React Router
- **Chatbot:** proxy a la API de Anthropic (Claude) desde el backend

## Roles

| Rol | Puede hacer |
|---|---|
| **Cliente** | Registrarse, cotizar (modelo del catálogo o propuesta personalizada), ver el estatus de sus cotizaciones y proyectos |
| **Trabajador** | Ver los proyectos que le asignó el administrador, actualizar su estado y % de avance, ver la cola general pendiente (solo lectura) |
| **Administrador** | Cargar/editar/eliminar productos del catálogo (con imagen), revisar y aprobar/rechazar cotizaciones (asignando trabajador al aprobar), dashboard de todos los pedidos, crear cuentas de trabajador |

**Usuarios de prueba** (creados por `seed.py`, cambia las contraseñas antes de producción):
```
administrador: admin@losmejia.com / cambiar123
trabajador:    trabajador@losmejia.com / cambiar123
cliente:       cliente@losmejia.com / cambiar123
```

## Estructura
```
herreria-los-mejia/
├── backend/
│   ├── app.py
│   ├── models.py       # Usuario, Producto, PrecioMaterial, Cotizacion, Proyecto
│   ├── auth.py          # sesión + decorador @requiere_rol
│   ├── seed.py
│   ├── uploads/         # imágenes del catálogo (se crea sola, no subir a git)
│   └── routes/
│       ├── auth.py       # login, registro, logout
│       ├── admin.py      # catálogo+imágenes, cotizaciones, proyectos, equipo
│       ├── trabajador.py
│       ├── cliente.py
│       ├── catalogo.py   # público
│       ├── cotizador.py  # público (se liga al cliente si hay sesión)
│       └── chatbot.py
└── frontend/
    └── src/
        ├── context/       # ThemeContext (claro/oscuro), AuthContext
        ├── pages/         # Login, Registro, paneles por rol
        └── components/
```

## 1. Correrlo en tu computadora

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env: DATABASE_URL (o deja sqlite:///local.db para probar sin
# Postgres), ANTHROPIC_API_KEY para el chatbot, y SECRET_KEY (cualquier
# cadena larga y aleatoria).

python seed.py                # carga catálogo, precios y usuarios de prueba
python app.py                 # levanta en http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # levanta en http://localhost:5173
```

## 2. Tema claro/oscuro
Aplica a todo el sitio (público y paneles). El botón está en el header;
la preferencia se guarda en el navegador de cada persona.

## 3. Imágenes del catálogo — persistencia en Railway
Las imágenes se guardan en `backend/uploads/` dentro del propio servidor
(no se usa ningún servicio externo, como pediste). **Importante:** el disco
de Railway es efímero — si no agregas un **Volume**, las imágenes se
borran cada vez que el servicio se redespliega.

Para hacerlo persistente en Railway:
1. En tu servicio backend → pestaña **Volumes** → **+ New Volume**.
2. Móntalo en la ruta `/app/uploads` (o donde quede tu carpeta de la app).
3. Agrega la variable de entorno `UPLOAD_FOLDER=/app/uploads` al servicio.

Sin esto, el sitio sigue funcionando normal — solo tendrías que volver a
subir las imágenes si el servicio se redespliega.

## 4. Publicarlo en Railway (backend + frontend como 2 servicios)

### Backend
1. Servicio → **Root Directory** = `backend`
2. Variables: `ANTHROPIC_API_KEY`, `SECRET_KEY` (una cadena aleatoria larga),
   `FRONTEND_ORIGIN` = la URL pública de tu servicio frontend (con `https://`,
   sin `/` al final) — **necesaria para que las cookies de sesión funcionen
   entre dominios distintos**.
3. Agrega PostgreSQL (**+ New → Database → PostgreSQL**), Railway conecta
   `DATABASE_URL` solo.
4. Genera el dominio público (**Settings → Networking → Generate Domain**).
5. Shell del servicio → `python seed.py` (una sola vez).
6. (Opcional pero recomendado) configura el Volume de la sección 3.

### Frontend
1. Nuevo servicio con el mismo repo → **Root Directory** = `frontend`
2. Build Command: `npm install && npm run build`
3. Start Command: `npm run start`
4. Variable: `VITE_API_URL` = la URL del backend (paso anterior)
5. Genera su dominio público.
6. **Si cambias `VITE_API_URL` después del primer build, tienes que hacer
   un Redeploy completo** — Vite incrusta esa variable en tiempo de
   compilación, no de ejecución.

### Verificar
- Catálogo carga con imágenes.
- Login con los usuarios de prueba de cada rol.
- Cliente cotiza → aparece en **Admin → Cotizaciones** → al aprobar
  (asignando trabajador) aparece en **Admin → Pedidos** y en el panel del
  trabajador asignado.
- Cambiar avance/estado desde el panel de trabajador se refleja en el
  panel del cliente.

## 5. Próximos pasos sugeridos
- Reemplazar productos/fotos/precios de ejemplo por los reales desde
  **Admin → Catálogo**.
- Cambiar las contraseñas de los usuarios de prueba (o crear las cuentas
  reales desde **Admin → Equipo** y desactivar/borrar las de ejemplo).
- Poner el teléfono, email y redes sociales reales en el Header y Footer.
