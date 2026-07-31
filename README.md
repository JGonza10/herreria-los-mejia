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

**Usuarios de prueba** (creados por `seed.py`):
```
administrador: admin@losmejia.com
trabajador:    trabajador@losmejia.com
cliente:       cliente@losmejia.com
```
Las contraseñas no viven en este repositorio: `seed.py` las toma de las
variables de entorno `SEED_ADMIN_PASSWORD`, `SEED_TRABAJADOR_PASSWORD` y
`SEED_CLIENTE_PASSWORD` (mínimo 12 caracteres cada una) y se niega a correr
si faltan. Ver `.env.example`.

## Contraseñas y sesiones
- `POST /api/auth/password` (logueado): cambia tu propia contraseña, pide la
  actual y la nueva.
- `PUT /api/admin/usuarios/<id>/password` (solo administrador): restablece la
  contraseña de cualquier usuario desde el panel de Equipo.
- **No hay recuperación de contraseña por correo, y es deliberado.** Para un
  taller de este tamaño no vale la pena la complejidad de correos
  transaccionales — si alguien olvida su contraseña, el administrador se la
  restablece desde el panel. Si el negocio crece a un punto donde esto ya no
  alcanza, se reconsidera.
- Los tokens de sesión no tienen estado y viven 30 días; cambiar una
  contraseña (por cualquiera de las dos vías de arriba) sube el
  `token_version` del usuario, lo que invalida de inmediato cualquier otro
  token que esa persona tuviera activo — la única forma barata de revocar
  una sesión sin mantener una lista negra de tokens.

## Especificación unificada de pieza (`backend/dominio/`)
Una sola estructura de datos (`spec`, guardada como JSON en `Cotizacion.spec`)
describe qué se va a fabricar, para que el dibujo, el precio y —más
adelante— la lista de corte lean de la misma fuente en vez de tener cada
uno su propia idea de qué es una pieza:
```json
{
  "version": 1,
  "tipo": "porton_corredizo",
  "sistema": "herreria",
  "medidas": { "ancho_m": 3.2, "alto_m": 2.4 },
  "piezas": 1,
  "estructura": {}, "relleno": {}, "herrajes": [],
  "acabado": "estandar",
  "notas": null
}
```
- `dominio/spec.py`: `construir_basico(...)` arma el spec a partir de lo que
  hoy captura el cotizador (material + medidas); `validar(spec)` lanza
  `ValueError` si algo no cuadra. El campo `version` existe desde ya —
  cuando la forma cambie, las cotizaciones viejas necesitan poder seguir
  leyéndose con la forma que tenían al crearse.
- `dominio/precios.py`: `calcular_precio()`, la misma función de siempre,
  reubicada para no depender de Flask.
- `GET /api/cotizador/tipos-trabajo`: catálogo de qué se puede fabricar
  (`TipoTrabajo`, tabla `tipos_trabajo`) — en base de datos, no en código,
  para poder agregar tipos sin redesplegar. Hoy el cotizador no pregunta el
  tipo todavía, así que cada cotización nueva se guarda como `"indefinido"`.
- `backend/migrar_specs.py`: backfill de una sola pasada para las
  cotizaciones creadas antes de que existiera esta columna. Seguro de correr
  más de una vez — solo toca las filas con `spec` nulo.

## Ficha de escalera: dibujo + 3D en el PDF
`POST /api/escalera/pdf` ya no entrega solo una tabla de números:
- **Alzado 2D acotado, en vectores** (`backend/ficha_dibujo.py`, con
  `reportlab.graphics.shapes`): la escalera a escala real, con las medidas
  totales marcadas, más una **silueta humana de 1.70 m** a la misma escala.
  No es decoración — es el detector de errores de captura más efectivo que
  hay: si alguien escribió 320 en vez de 3.20, la pieza sale veinte veces
  más alta que la persona y se nota antes de cortar el material.
- **Vista 3D incrustada** (opcional): el frontend captura el canvas de
  `Escalera3D.jsx` (`preserveDrawingBuffer: true` en el `WebGLRenderer` —
  sin esa bandera `toDataURL()` sale en blanco) y la manda como base64 en el
  mismo POST. Si la captura falla o llega corrupta, el PDF se genera igual,
  sin la imagen — nunca por eso se deja de entregar la ficha.
- Incluye el texto de qué NO cubre la ficha (obra civil, resane, pintura de
  muro, instalaciones eléctricas) y la vigencia de 30 días.

**Pendiente, no incluido en este alcance:** un solo endpoint de ficha para
cualquier tipo de pieza (hoy solo existe para escalera — las cotizaciones
del catálogo/personalizadas todavía no generan PDF, así que no había nada
que unificar) y el QR a la vista 3D interactiva (depende del link público
de aceptación de la Fase 7.1, que tampoco existe todavía).

## Tarifas versionadas (`backend/routes/tarifas.py`)
Antes de esto, la única forma de cambiar un precio era editar `seed.py`,
hacer commit y redesplegar — la razón número uno por la que un cotizador se
abandona a los tres meses (actualizar.md, Fase 4.2).

- `POST /api/admin/tarifas` — crea una tarifa nueva (`nombre`, `vigente_desde`).
- `PUT /api/admin/tarifas/<id>/precios` — reemplaza toda su lista de precios
  de una sola vez (concepto + clave + unidad + precio).
- `POST /api/admin/tarifas/<id>/activar` — la marca como la vigente
  (desactiva cualquier otra).
- `POST /api/admin/tarifas/<id>/duplicar` — copia una tarifa existente como
  punto de partida de la siguiente, con un `ajuste_pct` opcional para subir
  todo de un jalón ("copiar Julio 2026 a Agosto 2026 y subir todo 4 %").
- Todas las tablas son nuevas (`tarifas`, `precios_tarifa`); nada se borró.
- **Pantalla:** pestaña "Tarifas" del panel de administrador
  (`AdminTarifas.jsx`) — crear, editar precios en tabla, activar y duplicar
  con ajuste porcentual, todo desde el navegador.

## Partidas múltiples y cobro por sistema (Fase 4.1/4.3/4.4)
`POST /api/cotizador/solicitar` acepta ahora un cuerpo con `piezas` (lista) en
vez de una sola pieza — cada elemento es `{tipo, material, ancho_m, alto_m,
con_acabado, piezas, descripcion}`. Con eso:
- Cada pieza se cotiza con **la tarifa activa** (no `PrecioMaterial`) y con
  la estrategia de cobro de su sistema:
  - **Herrería**: m² × (precio base + acabado si aplica).
  - **Aluminio**: metros lineales de perfil (perímetro) + m² de cristal —
    dos precios que se mueven por separado.
  - **Cristal templado**: m² con **mínimo de fabricación** (`minimo_facturable`
    de `TipoTrabajo`) + canteado cobrado por perímetro, no por área. Una
    puerta de 40×40 cm ya no cuesta la sexta parte de una de 1×1 m.
  - **Cualquier tipo en `ml`** (barandal): por metro lineal, no por m² — la
    corrección de modelado que el plan marca como la más importante de esta
    fase. Por convención, `ancho_m` guarda la longitud para estos tipos.
- Se crea una `Partida` por pieza (con su propio `spec` y `desglose`), y la
  `Cotizacion` guarda `folio` (`LM-AAAA-NNNN`), `vigencia_hasta` (+30 días),
  `subtotal`, `descuento` e `iva` (16 % opcional) y `total`.
- Si no hay ninguna tarifa activa, responde 400 con un mensaje claro en vez
  de inventar un precio.
- **El flujo de una sola pieza sigue exactamente igual** (`Cotizador.jsx` no
  cambió): sin `piezas` en el cuerpo, usa `PrecioMaterial` como siempre, sin
  folio ni tarifa. Los dos caminos conviven en el mismo endpoint.
- `backend/migrar_partidas.py`: backfill de una sola pasada — convierte cada
  cotización vieja (sin partidas) en una cotización con una sola partida,
  usando el precio que ya tenía guardado (no recalcula nada).
- `POST /api/admin/cotizaciones/<id>/simular` (solo administrador): recalcula
  el precio con parámetros ajustables en vivo (mano de obra, flete, % de
  merma, % de utilidad, descuento, IVA) **sin guardar nada** hasta que el
  administrador confirme desde otra pantalla. Devuelve el **margen sobre
  venta** (no el % de utilidad sobre costo — son números distintos: 25%
  sobre costo es 20% sobre venta) y el estimado del cliente como **rango**
  (±10%), nunca como número exacto.

**Actualización:** ya existe la pantalla. `Cotizador.jsx` deja agregar
piezas adicionales ("+ Agregar otra pieza") — sin piezas extra, manda la
solicitud exactamente igual que siempre (`/solicitar` sin `piezas`); con una
o más, arma el arreglo `piezas` y usa el motor nuevo. El estimado se
muestra siempre como **rango ±10%**, nunca como número exacto (siguiendo la
recomendación del plan). `AdminCotizaciones.jsx` tiene el panel de
simulación por cotización (no guarda nada hasta que el admin confirme por
otro lado). Validado con `vite build` y con una petición real de extremo a
extremo contra el backend (ver commit correspondiente) — no se probó en un
navegador real, este entorno no tiene uno disponible.

## Lista de corte y requisición de material (Fase 5)
`backend/dominio/despiece.py` saca de la especificación de una partida
cuántos tramos de perfil hacen falta (marco perimetral + barrotes
verticales + travesaños) y los acomoda en barras comerciales de 6 m con
*first-fit decreasing* — diez líneas resuelven el 90 % del beneficio, no
hace falta un solver.

- `POST /api/admin/partidas/<id>/despiece` — la lista de corte en JSON, más
  la **merma real calculada contra la teórica que se cobró**. Si el taller
  cobra 7 % de merma y en realidad desperdicia 14 %, está perdiendo dinero
  en cada trabajo y hoy no había forma de saberlo.
- `GET /api/admin/partidas/<id>/orden-trabajo.pdf` — PDF para el trabajador:
  lista de corte y herrajes, **sin precios** (el trabajador no los necesita
  y el cliente no debe verlos si la hoja se queda en la obra). Todavía sin
  el alzado 2D de la pieza — depende del dibujo paramétrico genérico de la
  Fase 6.
- `GET /api/admin/requisicion` — suma las barras de 6 m que hacen falta en
  todos los proyectos activos (`pendiente`/`en_proceso`), para comprar una
  vez en vez de ir al proveedor cada vez que se corta un trabajo. Hoy es un
  total agregado, no una lista por calibre — el spec actual no captura qué
  perfil específico usa cada pieza.
- Aplica a piezas rectangulares con marco (portones, rejas, protecciones,
  barandal); respeta `TipoTrabajo.admite_barrotes` para no inventar
  barrotes en cancelería o vidrio. No aplica a escalera, que tiene su
  propia geometría (`dominio/geometria.py`, Fase 3).
- Si no se capturó `separacion_barrotes_cm`, usa 12 cm por defecto (el
  mismo valor del ejemplo de la Fase 2) — es un despiece de referencia, no
  el definitivo del taller, hasta que el formulario capture esos datos.
- **Ya tiene pantalla:** dentro del detalle de cada proyecto en
  `AdminPedidos.jsx`, por partida — botones "Ver lista de corte" y
  "Descargar orden de trabajo (PDF)". `AdminRequisicion.jsx` es la pestaña
  nueva del panel para el total agregado.

## 3D paramétrico para el resto del catálogo (Fase 6)
`Escalera3D.jsx` (three.js puro) demostró que la capacidad ya estaba en el
proyecto — el problema era que solo existía para escaleras. Ahora:

- **`frontend/src/components/Pieza3D.jsx`**: componente genérico que recibe
  la especificación unificada de pieza y arma la escena — un constructor
  por `modo_dibujo` (`barrotes`, `cancel`, `vidrio`, `estructura`), mismo
  patrón `CONSTRUCTORES[tipo]` que ya usaba `Escalera3D.jsx`. Cristal con
  transparencia real (`MeshPhysicalMaterial` + `transmission`, no un color
  plano). Zoom con la rueda del ratón y gesto de pinza en móvil — y se lo
  agregué también a `Escalera3D.jsx`, que antes solo rotaba.
- **`frontend/src/components/Pieza2D.jsx`**: el alzado acotado en SVG,
  compartiendo la misma convención geométrica (separación de barrotes,
  marco perimetral) que `Pieza3D.jsx` y que `dominio/despiece.py` — si el
  dibujo de pantalla y el de la lista de corte no coincidieran, se pierde
  la confianza en los dos.
- Conectado como vista previa en `Cotizador.jsx` (2D + 3D lado a lado, en
  vivo mientras se llena el formulario) sin tocar el flujo de envío
  existente — el modo de dibujo se infiere del material elegido
  (hierro→barrotes, aluminio→cancel, vidrio→vidrio) porque el cotizador
  todavía no pregunta el tipo de trabajo explícitamente.
- Limpieza de recursos (`renderer.dispose()`, geometrías y materiales) en
  ambos componentes al desmontar.

**Pendiente, no incluido en este alcance:** cotas visibles dentro de la
propia escena 3D (hoy solo están en el alzado 2D) — requeriría texto en la
escena (sprites o `CSS2DRenderer`), una dependencia/complejidad adicional
que no se justificó todavía. **Importante:** estos cambios de frontend se
validaron con `vite build` (compila sin errores) y revisión de código, pero
**no se probaron en un navegador real** — este entorno no tiene uno
disponible. Antes de dar por buena la vista previa, ábrela en `npm run dev`
y confirma que rota, hace zoom y se ve razonable con medidas reales.

## Operación del taller (Fase 7)

**7.1 — Aceptación por el cliente.** Cada cotización trae un `token_publico`
firmado (`itsdangerous`, igual que los tokens de sesión — nada nuevo que
mantener). `GET /api/cotizador/publica/<token>` (sin login) muestra la
ficha; `POST .../aceptar` guarda fecha, hora e IP de la aceptación
(`Cotizacion.aceptada_en/aceptada_ip`). No es un contrato ante notario, pero
es mejor que "usted me dijo que sí por teléfono". Una cotización vencida
(`vigencia_hasta` pasada) no se puede aceptar.

**7.2 — Anticipos y estado de cuenta.** Tabla `Pago` (monto, método, fecha,
comprobante). `POST /api/admin/proyectos/<id>/pagos` registra uno.
**Ningún proyecto puede pasar a `en_proceso` sin al menos un pago
registrado** — la regla se aplica igual desde el panel de admin y desde el
panel de trabajador, y evita el problema más caro de un taller chico:
comprar material para un trabajo que se cayó. `Proyecto.to_dict()` incluye
`total_pagado` y `saldo`. No se integró pasarela de pagos en línea
(decisión explícita del plan original, sección "Lo que no recomiendo").

**7.3 — Seguimiento con fotos.** Tabla `FotoAvance`. `POST
/api/trabajador/proyectos/<id>/fotos` (multipart, reutiliza el
`guardar_imagen` que ya existía para el catálogo) — solo el trabajador
asignado puede subir. La compresión del lado del cliente
(`canvas.toBlob` calidad 0.7) queda pendiente en el frontend, que no se
tocó en este alcance.

**7.4 — Vigencia y seguimiento.** `backend/vencer_cotizaciones.py`: script
para correr una vez al día (Cron Job de Railway) que marca `estado=vencida`
a lo que ya pasó su `vigencia_hasta` sin ser aceptado ni rechazado.
`POST /api/admin/cotizaciones/<id>/revivir` la reactiva recalculando con la
tarifa **activa**, no con la vieja. `GET /api/admin/cotizaciones/seguimiento`
agrupa lo que no ha tenido respuesta en baldes de 3/7/15+ días — la mayoría
de las cotizaciones no se pierden por precio, se pierden por falta de
seguimiento. El listado de cotizaciones también trae un `link_whatsapp`
prellenado (`wa.me`, un `<a href>`, no una integración).

**7.5 — Agenda y capacidad.** Al aprobar una cotización, `fecha_estimada_entrega`
se calcula a partir de la carga real de los proyectos activos (constante
`CAPACIDAD_SEMANAL` en `routes/admin.py` — ajustable, no hay pantalla de
configuración todavía), no del optimismo. `GET /api/admin/agenda` agrupa
los proyectos activos por semana de entrega y marca si alguna semana está
sobrecargada.

**7.6 — Bitácora de auditoría.** Tabla `Bitacora` (`usuario_id`, `entidad`,
`entidad_id`, `accion`, `antes`, `despues`). Conectada en los cambios de
precio y activación de tarifa, y en los cambios de estado y asignación de
proyecto (desde admin y desde trabajador). `GET /api/admin/bitacora`
(filtrable por `entidad`/`entidad_id`) responde "¿quién le bajó el precio a
esta cotización?".

**Actualización:** ya existen las pantallas — página pública en
`/cotizacion/:token` (`CotizacionPublica.jsx`) con el botón de aceptar;
formulario de registrar pago y galería de fotos dentro del detalle de cada
proyecto en `AdminPedidos.jsx`; tablero de seguimiento y botón de WhatsApp
en `AdminCotizaciones.jsx`; `AdminAgenda.jsx` y `AdminBitacora.jsx` como
pestañas nuevas del panel. El trabajador sube sus propias fotos y registra
horas desde `TrabajadorPanel.jsx`; el cliente ve sus fotos de avance y su
saldo desde `ClientePanel.jsx`.

## Los números del negocio (Fase 8)
Todo lo anterior recopila datos; esta fase los usa (`backend/reportes.py`).

- **8.1 Costo real contra cotizado** (`GET /api/admin/reportes/costo-real`)
  — el único reporte que realmente importa. `Proyecto.costo_material_real`
  se captura a mano al conciliar (no hay integración de compras); la mano
  de obra se valora con las horas registradas (8.3) × `COSTO_HORA_ASUMIDO`
  ($120/hora, ajustable en `reportes.py`). Mientras no se capture el costo
  real, el reporte devuelve `null` en vez de inventar un número.
- **8.2 Tasa de conversión** (`GET /api/admin/reportes/conversion`) por tipo
  de trabajo y por rango de precio (`$0–5,000`, `$5,000–15,000`,
  `$15,000–30,000`, `$30,000+`) — si el 90% de los portones se aprueban y
  el 20% de los canceles, hay algo que corregir en el precio del cancel o
  en cómo se presenta.
- **8.3 Horas por m²** — tabla `RegistroHoras`; `POST
  /api/trabajador/proyectos/<id>/horas` (el trabajador registra sus propias
  horas). `GET /api/admin/reportes/horas-por-m2` calcula el real contra el
  `320 $/m²` que hoy es un número inventado.
- **8.4 Exportar a Excel** (`GET /api/admin/reportes/excel`, `XlsxWriter`,
  ya estaba instalado): un libro con las 4 hojas de arriba, para el
  contador.

**Actualización:** ya existen las pantallas. El trabajador registra horas
desde `TrabajadorPanel.jsx`; el administrador captura el costo real y ve
las 4 tablas de reportes (con el botón de exportar a Excel) desde
`AdminPedidos.jsx` y la pestaña nueva `AdminReportes.jsx`. Con esto se
cierran las 8 fases de `actualizar.md` — backend y frontend.

## Estructura
```
herreria-los-mejia/
├── backend/
│   ├── app.py
│   ├── models.py       # Usuario, Producto, PrecioMaterial, Cotizacion, TipoTrabajo, Proyecto
│   ├── auth.py          # sesión + decorador @requiere_rol
│   ├── seed.py
│   ├── uploads/         # imágenes del catálogo (se crea sola, no subir a git)
│   ├── dominio/         # motor de precios y spec — sin Flask, sin db.session
│   │   ├── precios.py    # calcular_precio(): la misma lógica de siempre, reubicada
│   │   └── spec.py       # especificación unificada de pieza (ver más abajo)
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
# Postgres), ANTHROPIC_API_KEY para el chatbot, SECRET_KEY (cualquier
# cadena larga y aleatoria), y SEED_ADMIN_PASSWORD / SEED_TRABAJADOR_PASSWORD
# / SEED_CLIENTE_PASSWORD (mínimo 12 caracteres) para los usuarios de prueba.

flask --app app db upgrade    # crea/actualiza el esquema (Alembic)
python seed.py                # carga catálogo, precios y usuarios de prueba
python app.py                 # levanta en http://localhost:5000
```

### Migraciones (Alembic)
El esquema se maneja con Flask-Migrate, no con `db.create_all()`. Cada vez
que cambien los modelos en `models.py`:
```bash
flask --app app db migrate -m "descripción del cambio"   # revisa el archivo generado en migrations/versions/ ANTES de aplicarlo
flask --app app db upgrade
```
En Railway, el `Procfile` ya corre `flask --app app db upgrade` antes de
levantar `gunicorn` en cada deploy.

### Pruebas
```bash
pip install -r requirements-dev.txt
pytest
```
Cubre el motor de precios del cotizador y las 4 calculadoras de escalera
con casos de referencia (medidas conocidas → total/resultado esperado).
Si una prueba truena después de tocar `cotizador.py` o `escalera.py`, es
porque el cambio alteró un número que un cliente ya vio en una cotización.

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

## Observabilidad y respaldos
- **Logging estructurado a stdout:** cada petición queda en los logs
  (método, ruta, código de respuesta) y cualquier error no manejado se
  registra completo con `app.logger.exception` antes de responder un 500
  genérico — así "me marcó error" se puede investigar después. Railway
  captura stdout automáticamente, se ve en la pestaña **Logs** del servicio.
- **Sentry** (plan gratuito) da alertas en tiempo real y agrupa errores
  repetidos — no está integrado todavía porque requiere una cuenta propia.
  Si se quiere agregar: `pip install sentry-sdk[flask]`, y en `app.py`,
  `sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])` antes de crear la app.
- **Respaldos de PostgreSQL:** confirma en el dashboard de Railway (plan del
  servicio de PostgreSQL) si ya incluye respaldos automáticos. Si no,
  `backend/respaldar_db.py` genera un dump manual:
  ```bash
  DATABASE_URL="<la url real de producción>" python respaldar_db.py
  ```
  Prográmalo semanal (Programador de tareas de Windows, cron, o un Cron Job
  de Railway) y guarda el resultado fuera de Railway (un bucket, o hasta
  Drive) — la lista de precios y el historial de cotizaciones del taller no
  existen en ningún otro lado.
- **`MAX_CONTENT_LENGTH`** de 8 MB en la app: una subida más grande responde
  413 antes de procesarse entera, en vez de tumbar el servicio.

Sin esto, el sitio sigue funcionando normal — solo tendrías que volver a
subir las imágenes si el servicio se redespliega.

## 4. Publicarlo en Railway (backend + frontend como 2 servicios)

### Backend
1. Servicio → **Root Directory** = `backend`
2. Variables: `ANTHROPIC_API_KEY`, `SECRET_KEY` (una cadena aleatoria larga),
   `FRONTEND_ORIGIN` = la URL pública de tu servicio frontend (con `https://`,
   sin `/` al final) — **necesaria para que las cookies de sesión funcionen
   entre dominios distintos**.
   El endpoint del chatbot ya limita peticiones por IP (20/hora, 100/día) y
   trunca el historial, pero eso no reemplaza poner un **límite de gasto
   mensual** para `ANTHROPIC_API_KEY` en console.anthropic.com — es la única
   protección que no depende de que el código esté bien.
3. Agrega PostgreSQL (**+ New → Database → PostgreSQL**), Railway conecta
   `DATABASE_URL` solo.
4. Genera el dominio público (**Settings → Networking → Generate Domain**).
5. Antes de correr el seed, agrega `SEED_ADMIN_PASSWORD`,
   `SEED_TRABAJADOR_PASSWORD` y `SEED_CLIENTE_PASSWORD` (mínimo 12
   caracteres, distintas entre sí) como variables del servicio — luego
   Shell del servicio → `python seed.py` (una sola vez). Puedes borrar esas
   tres variables después de correrlo.
6. (Opcional pero recomendado) configura el Volume de la sección 3.
7. **Solo la primera vez que despliegas este `Procfile` con Alembic**, si el
   servicio ya tenía tablas creadas por el antiguo `db.create_all()`: antes
   de que corra el deploy nuevo, saca un respaldo (`pg_dump`) y marca la
   base como si ya tuviera la migración inicial aplicada —
   `flask --app app db stamp head` apuntando a la `DATABASE_URL` real —
   o Alembic va a intentar crear tablas que ya existen y va a fallar.
   Verifica con `flask --app app db current`. Después de este paso único,
   los deploys siguientes solo corren `db upgrade` normal.

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
