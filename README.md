# Herrería Los Mejía — Sitio web

Sitio web para la herrería "Los Mejía" (hierro, aluminio y vidrio):
catálogo de productos, cotizador por m², chatbot conectado a IA, y redes
sociales.

## Stack
- **Backend:** Flask + SQLAlchemy + PostgreSQL
- **Frontend:** React + Vite
- **Chatbot:** proxy a la API de Anthropic (Claude) desde el backend

## Estructura
```
herreria-los-mejia/
├── backend/       # API Flask
│   ├── app.py
│   ├── models.py
│   ├── seed.py    # datos de ejemplo (catálogo + precios)
│   └── routes/
└── frontend/      # React + Vite
    └── src/
```

## 1. Correrlo en tu computadora

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env: pon tu DATABASE_URL (o deja sqlite:///local.db para probar
# sin Postgres) y tu ANTHROPIC_API_KEY para el chatbot.

python seed.py                # carga catálogo y precios de ejemplo
python app.py                 # levanta en http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # levanta en http://localhost:5173
```
El frontend en modo desarrollo redirige automáticamente `/api/*` hacia
`http://localhost:5000` (ver `vite.config.js`).

## 2. Datos de ejemplo
`backend/seed.py` carga:
- Precios base por m² para hierro, aluminio y vidrio (editables en la tabla `precios_material`).
- 6 productos de catálogo de ejemplo (2 por material).

**Antes de publicar el sitio real**, reemplaza estos datos con tus productos,
fotos y precios reales — directamente en la base de datos o adaptando
`seed.py`.

## 3. Chatbot con IA
El endpoint `/api/chatbot/mensaje` llama a la API de Anthropic usando la
variable de entorno `ANTHROPIC_API_KEY` (nunca se expone al navegador).
Sin esa variable configurada, el chatbot responde con un aviso en vez de
fallar en silencio.

## 4. Publicarlo en Railway (backend + frontend como 2 servicios)

Railway permite tener varios servicios dentro del mismo proyecto, cada uno
apuntando a una subcarpeta del repo (monorepo). Así vamos a desplegar este
sitio: un servicio para `backend/` y otro para `frontend/`.

### Paso 0 — Subir el proyecto a GitHub
```bash
cd herreria-los-mejia
git init
git add .
git commit -m "Sitio Los Mejía: catálogo, cotizador y chatbot"
```
Crea un repo vacío en github.com (ej. `herreria-los-mejia`), luego:
```bash
git remote add origin https://github.com/JGonza10/herreria-los-mejia.git
git branch -M main
git push -u origin main
```

### Paso 1 — Crear el proyecto en Railway
1. Entra a [railway.app](https://railway.app) → **New Project**.
2. **Deploy from GitHub repo** → autoriza Railway → selecciona `herreria-los-mejia`.
3. Railway crea un primer servicio; lo vamos a configurar como el **backend**.

### Paso 2 — Configurar el servicio backend
1. Click en el servicio → pestaña **Settings**.
2. **Root Directory** → `backend`
3. Railway detecta el `Procfile` (`web: gunicorn app:app`) automáticamente.
4. Pestaña **Variables** → agrega:
   - `ANTHROPIC_API_KEY` = tu API key de Anthropic
5. Click **"+ New"** dentro del proyecto → **Database → PostgreSQL**. Railway
   conecta `DATABASE_URL` automáticamente al servicio backend.
6. Una vez que el deploy termine, copia el dominio público del backend
   (Settings → **Networking** → **Generate Domain**), algo como
   `herreria-backend-production.up.railway.app`.
7. Carga los datos de ejemplo una sola vez: pestaña del servicio → **Shell** → `python seed.py`.

### Paso 3 — Configurar el servicio frontend
1. En el mismo proyecto de Railway: **"+ New" → GitHub Repo** (el mismo repo otra vez).
2. En **Settings** de este nuevo servicio:
   - **Root Directory** → `frontend`
   - **Build Command** → `npm install && npm run build`
   - **Start Command** → `npm run start` (ya está en el `Procfile`)
3. Pestaña **Variables** → agrega:
   - `VITE_API_URL` = la URL del backend que copiaste en el paso anterior, con `https://` al inicio (ej. `https://herreria-backend-production.up.railway.app`)
4. Genera el dominio público de este servicio también (Networking → Generate Domain). Esa es la URL que compartes con tus clientes.

### Paso 4 — Verificar
- Abre la URL del frontend → deberías ver el sitio completo.
- Prueba el cotizador (calcula y envía una solicitud de prueba).
- Prueba el chatbot.
- Si algo no carga, revisa **Logs** del servicio correspondiente en Railway.

### Deploys futuros
```bash
git add .
git commit -m "descripción del cambio"
git push
```
Railway redespliega ambos servicios automáticamente con cada push.

## 5. Próximos pasos sugeridos
- Reemplazar productos/fotos/precios de ejemplo por los reales.
- Poner el número real de WhatsApp y redes sociales en `frontend/src/components/Footer.jsx`.
- Si quieres ver las cotizaciones recibidas, hay un endpoint interno `GET /api/cotizador/solicitudes` (sin panel visual todavía — se puede agregar un dashboard simple si lo necesitas).
