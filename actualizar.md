# actualizar.md — Plan de mejoras

**Proyecto:** Herrería Los Mejía · sitio + cotizador + simulación 2D/3D
**Repo:** `JGonza10/herreria-los-mejia`
**Base analizada:** ~4,300 líneas · Flask + SQLAlchemy + PostgreSQL · React 18 + Vite · three.js 0.160 · 2 servicios en Railway
**Fecha del análisis:** 29 de julio de 2026

---

## Cómo leer este documento

Las fases están en orden de dependencia, no de dificultad. La Fase 0 se hace hoy.
La Fase 2 es la que desbloquea casi todo lo demás: si se salta, las fases 3, 5 y 6
se convierten en tres implementaciones paralelas del mismo problema.

Cada punto trae **por qué**, no solo **qué**. Si el por qué no aplica al negocio real,
bórrenlo del plan sin culpa. Un plan que no se puede recortar no es un plan.

Notación: `⬛` bloquea otras fases · `⚠` riesgo de dinero o seguridad · `💰` impacto comercial directo

---

## Lo que ya está bien y no hay que tocar

Antes de la lista de cambios, conviene ser explícito sobre lo que está bien resuelto,
porque la tentación de reescribir es el mayor riesgo de un proyecto en este punto:

- **`backend/routes/escalera.py`** — Las validaciones contra el Reglamento de
  Construcciones de CDMX y la Ley de Blondel están bien planteadas, con las fuentes
  citadas en el docstring y una advertencia explícita de que no sustituye un cálculo
  estructural certificado. Ese criterio es el estándar a replicar en el resto del sistema.
- **La separación por blueprints** en `backend/routes/` está limpia y aguanta crecer.
- **La decisión de token firmado en vez de cookie** (`backend/auth.py`) está bien
  razonada y documentada — los navegadores efectivamente bloquean cookies cross-site
  entre dos dominios distintos de Railway. Fue la decisión correcta.
- **El fallback a SQLite** para desarrollo local baja muchísimo la fricción de arranque.
- **El manejo del `postgres://` → `postgresql+psycopg://`** en `app.py`, con el comentario
  explicando por qué psycopg2 falla en el builder de Railway. Ese comentario le va a
  ahorrar horas a quien toque esto en un año.

---

# FASE 0 — Urgente (hoy)

## 0.1 ⚠ Contraseñas de prueba expuestas

`README.md` publica `admin@losmejia.com / cambiar123` en un repositorio **público**, y
`backend/seed.py` crea esas cuentas. Si `seed.py` corrió en producción y las contraseñas
no se cambiaron, cualquiera que encuentre el repo entra como administrador.

- [ ] Cambiar las tres contraseñas en producción **ahora**.
- [ ] Quitar las credenciales del README; dejar solo los correos y una nota de que la
      contraseña se define al correr el seed.
- [ ] Modificar `seed.py` para que lea las contraseñas de variables de entorno y falle
      ruidosamente si no están:

```python
import os, sys

def password_requerido(nombre_var):
    valor = os.environ.get(nombre_var)
    if not valor or len(valor) < 12:
        sys.exit(f"Falta {nombre_var} (mínimo 12 caracteres). El seed no corre sin ella.")
    return valor
```

## 0.2 ⚠ `SECRET_KEY` con valor por defecto

`backend/app.py` cae a `"clave-de-desarrollo-cambiar-en-produccion"` si la variable no
está puesta. Ese string está en GitHub. Como `SECRET_KEY` firma los tokens de sesión,
quien lo tenga puede fabricar un token de administrador válido.

- [ ] Confirmar en Railway que `SECRET_KEY` está definida en el servicio backend.
- [ ] Hacer que la app se niegue a arrancar en producción sin ella:

```python
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("RAILWAY_ENVIRONMENT"):   # o cualquier bandera de producción
        raise RuntimeError("SECRET_KEY no está definida. La app no arranca sin ella.")
    SECRET_KEY = "solo-desarrollo-local"
```

Fallar al arrancar es preferible a arrancar insegura. Un servicio caído se nota en
minutos; una firma débil no se nota nunca.

## 0.3 ⚠ 💰 El chatbot es un endpoint público sin límite

`POST /api/chatbot/mensaje` no tiene autenticación, ni límite de peticiones, ni tope al
tamaño de `historial`. El endpoint reenvía a la API de Anthropic con la llave del taller.
Cualquiera con la URL puede usar esa llave de forma indefinida, y la factura llega a
tu papá.

- [ ] Limitar peticiones por IP (`Flask-Limiter`, p. ej. 20/hora y 100/día).
- [ ] Truncar `historial` a los últimos ~10 mensajes y validar que cada `content`
      no pase de unos 2,000 caracteres.
- [ ] Validar que cada elemento tenga `role` en `{"user", "assistant"}` — hoy se
      reenvía tal cual lo que manda el navegador.
- [ ] Poner un límite de gasto mensual en la consola de Anthropic. Es la única
      protección que no depende de que el código esté bien.

## 0.4 Limpieza del repositorio

- [ ] Borrar `fix-auth-token.patch`, `fix-auth-token-v2.patch`, `fix-errores-admin.patch`.
      Los parches ya aplicados viven en el historial de git, no en la raíz.
- [ ] Borrar `frontend/src/pages/admin/package.json` — un `package.json` dentro de una
      carpeta de páginas confunde a las herramientas y no hace nada.
- [ ] Decidir qué pasa con `Imagenes/` en la raíz: si son imágenes de ejemplo del
      catálogo, van a `backend/seed_assets/`; si no se usan, se borran.

---

# FASE 1 — Cimientos técnicos

Nada de esto se ve en la pantalla. Todo esto determina si las fases siguientes tardan
una semana o un mes.

## 1.1 ⬛ Migraciones con Alembic

Hoy el esquema se crea con `db.create_all()` en `app.py`. Eso funciona una sola vez:
crea tablas que no existen y **jamás modifica** las que ya existen. En el momento en que
se agregue una columna a `cotizaciones`, la base de producción se queda atrás sin avisar,
y el síntoma va a ser un error de columna inexistente en runtime.

Las fases 2 a 8 agregan columnas y tablas en cada una. Meter Alembic ahora cuesta una
tarde; meterlo después de tener datos reales del taller cuesta un fin de semana y un susto.

```bash
pip install Flask-Migrate==4.0.7
```

```python
# backend/extensions.py
from flask_migrate import Migrate
migrate = Migrate()

# backend/app.py, dentro de create_app()
migrate.init_app(app, db)
# y quitar el bloque:  with app.app_context(): db.create_all()
```

```bash
flask db init
flask db migrate -m "esquema inicial"   # revisar el archivo generado ANTES de aplicar
flask db upgrade
```

- [ ] Documentar en el README que cada deploy corre `flask db upgrade`.
- [ ] En Railway, agregarlo al comando de arranque:
      `flask db upgrade && gunicorn app:app`

**Advertencia:** la primera migración contra una base que ya tiene las tablas creadas por
`create_all()` hay que marcarla con `flask db stamp head` en vez de aplicarla, o Alembic
va a intentar crear tablas que ya existen.

## 1.2 Validación de entrada

`backend/routes/admin.py` hace `float(precio)` sin protección: un precio no numérico
tumba la petición con un 500 y un stack trace en los logs. El patrón se repite en varias
rutas. Con pocas rutas es tolerable; con las que faltan, no.

- [ ] Adoptar `pydantic` v2 para los cuerpos de petición (una clase por endpoint) o,
      si se prefiere no agregar dependencias, un helper propio:

```python
def numero(valor, campo, minimo=0, maximo=None):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"'{campo}' debe ser un número.")
    if n < minimo or (maximo is not None and n > maximo):
        raise ValueError(f"'{campo}' fuera de rango.")
    return n
```

- [ ] Registrar un manejador global de errores para que un `ValueError` de validación
      salga como 400 con mensaje legible, y cualquier otra excepción salga como 500
      genérico sin filtrar detalles internos.
- [ ] Validar medidas con rangos del mundo real: ancho ≤ 15 m, alto ≤ 6 m. Hoy se acepta
      un portón de 999 metros y se guarda en la base.

## 1.3 Pruebas del motor de precios

Es la única parte del sistema donde un error se convierte directamente en dinero perdido
o en un cliente enojado. También es la parte más fácil de probar, porque es matemática pura.

- [ ] `pytest` con pruebas de referencia: para un conjunto de casos conocidos
      (portón 3.20 × 2.40 en PTR cal. 18, cancel de 6 ventanas, barandal de 6 m),
      fijar el total esperado y que la prueba truene si cambia.
- [ ] Lo mismo para `escalera.py`: una escalera recta de 2.80 m de altura debe dar
      siempre el mismo número de escalones y las mismas advertencias.

Cuando lleguen las fases 2 y 4, estas pruebas son la red que permite refactorizar sin miedo.

## 1.4 Contraseñas y sesiones — lo que falta

- [ ] **No existe cambio de contraseña.** Las rutas de `auth.py` son registro, login,
      logout y "yo". Un trabajador que quiere cambiar su contraseña no puede.
      Agregar `POST /api/auth/password` (pide la actual y la nueva).
- [ ] **No existe recuperación de contraseña.** Para un taller pequeño, la vía práctica
      es que el administrador la restablezca desde el panel de Equipo, sin correos
      transaccionales. Documentarlo como decisión deliberada, no como pendiente.
- [ ] **Los tokens no se pueden revocar.** Son sin estado y viven 30 días; `logout` solo
      los borra del navegador. Si a alguien le roban el token, sigue siendo válido un mes.
      Solución barata: una columna `token_version` en `usuarios`, incluida en el token y
      verificada al validarlo. Cambiarla invalida todas las sesiones de esa persona.

## 1.5 Observabilidad y respaldos

- [ ] Sentry (plan gratuito) o al menos logging estructurado a stdout. Hoy, si un cliente
      dice "me marcó error", no hay forma de saber qué pasó.
- [ ] Confirmar si el plan de Railway incluye respaldos automáticos de PostgreSQL.
      Si no, un `pg_dump` semanal a un bucket o incluso a Drive. La lista de precios y el
      historial de cotizaciones del taller no existen en ningún otro lado.
- [ ] `MAX_CONTENT_LENGTH` en la app (p. ej. 8 MB) para las subidas de imágenes.
- [ ] Índices en `cotizaciones(cliente_id)`, `cotizaciones(estado, creado_en)` y
      `proyectos(trabajador_id, estado)`. Con 200 registros no importa; con 20,000 sí.

---

# FASE 2 ⬛ — La especificación unificada de pieza

**Esta es la fase central del plan.**

Hoy el sistema tiene dos mundos que no se hablan:

- `routes/cotizador.py` sabe de precios pero no de geometría: para él una pieza es
  `material + ancho + alto`.
- `routes/escalera.py` sabe de geometría pero no de precios: calcula escalones, huellas
  y advertencias normativas, y no cotiza nada.

Y ninguno de los dos sabe qué **tipo de trabajo** es. Un portón y una protección de
ventana del mismo material y las mismas medidas cuestan lo mismo en el cotizador actual,
lo cual es falso en cualquier taller.

## 2.1 La idea

Una sola estructura de datos —la **especificación de pieza**— que describa qué se va a
fabricar, y de la cual salgan cuatro cosas distintas:

```
                    ┌─→ dibujo 2D acotado (pantalla y PDF)
  especificación ───┼─→ modelo 3D (pantalla)
    de pieza        ├─→ precio con desglose
                    └─→ lista de corte (taller)
```

Si esta estructura se define bien una vez, las fases 3, 5 y 6 son tres consumidores de lo
mismo. Si no se define, son tres implementaciones que se van a contradecir entre sí.

## 2.2 Forma de la especificación

Guardarla como `JSONB` en PostgreSQL. Es un dato que va a cambiar de forma mientras el
negocio aprende qué necesita, y no vale la pena normalizar cada campo en columnas todavía.

```json
{
  "version": 1,
  "tipo": "porton_corredizo",
  "sistema": "herreria",
  "medidas": { "ancho_m": 3.20, "alto_m": 2.40 },
  "piezas": 1,
  "estructura": {
    "perfil": "ptr_1.5_cal14",
    "separacion_barrotes_cm": 12,
    "travesanos": 2,
    "divisiones_verticales": 0
  },
  "relleno": { "tipo": "barrotes", "cristal_mm": null },
  "acabado": "galvanizado",
  "herrajes": [
    { "clave": "motor_corredizo", "cantidad": 1 },
    { "clave": "chapa_sobreponer", "cantidad": 1 }
  ],
  "notas": "Va sobre banqueta con pendiente."
}
```

Decisiones detrás de esa forma:

- **`version`** desde el día uno. Cuando la estructura cambie —y va a cambiar— las
  cotizaciones viejas tienen que seguir dibujándose y reproduciéndose. Sin este campo,
  un cambio de forma rompe el historial en silencio.
- **`sistema`** (`herreria` | `aluminio` | `cristal_templado`) separado de `tipo` porque
  determina **cómo se cobra**, no qué es. Ver 4.3.
- **Medidas siempre en metros**, en todo el sistema, sin excepción. La única unidad
  distinta permitida es la separación de barrotes en centímetros, porque así la dice el
  herrero, y pelearse con el vocabulario del taller es una batalla perdida.

## 2.3 Catálogo de tipos de trabajo

Nueva tabla, no un enum en el código, porque el dueño tiene que poder agregar tipos sin
tocar el código ni redesplegar:

```python
class TipoTrabajo(db.Model):
    __tablename__ = "tipos_trabajo"

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(40), unique=True, nullable=False)   # porton_corredizo
    nombre = db.Column(db.String(80), nullable=False)               # Portón corredizo
    sistema = db.Column(db.String(20), nullable=False)              # herreria|aluminio|cristal
    unidad = db.Column(db.String(4), nullable=False)                # m2 | ml
    altura_referencia_m = db.Column(db.Numeric(4, 2), nullable=True) # solo si unidad = ml
    modo_dibujo = db.Column(db.String(20), nullable=False)          # barrotes|cancel|vidrio|estructura
    admite_barrotes = db.Column(db.Boolean, default=True)
    minimo_facturable = db.Column(db.Numeric(5, 2), default=1)
    activo = db.Column(db.Boolean, default=True)
```

Semillas mínimas para arrancar: portón corredizo, portón abatible, reja o cerca,
protección para ventana, barandal, cancelería, ventana de aluminio, puerta de cristal
templado, escalera.

**El barandal se cobra por metro lineal, no por m².** Es la corrección de modelado más
importante de esta fase: hoy todo el sistema asume m², y eso hace que un barandal de
6 metros por 1 metro de alto se cotice como 6 m² cuando el taller lo cobra como 6 metros
lineales con una altura de referencia. Son números distintos y el cliente lo va a notar.

## 2.4 Dónde vive el motor

Sacar el cálculo de las rutas a un módulo propio, sin dependencias de Flask:

```
backend/
  dominio/
    __init__.py
    spec.py         # validación y normalización de la especificación
    precios.py      # cotizar(spec, tarifas, config) -> Desglose
    geometria.py    # spec -> primitivas de dibujo (compartido por 2D y 3D)
    despiece.py     # spec -> lista de corte
```

Funciones puras: entra un diccionario, sale un diccionario. Sin `request`, sin `db.session`,
sin `current_app`. Eso las hace probables en milisegundos, reutilizables desde el generador
de PDF y desde un script de línea de comandos, y —lo que más importa a 20 años— entendibles
por quien las lea sin tener que cargar el resto de la aplicación en la cabeza.

- [ ] Reescribir `calcular_precio()` de `routes/cotizador.py` como `dominio/precios.py`,
      manteniendo la ruta vieja funcionando contra el motor nuevo.
- [ ] Migrar los datos existentes: para cada `Cotizacion` vieja, construir su `spec`
      a partir de `material`, `ancho_m` y `alto_m`, con `tipo` inferido del producto del
      catálogo o marcado como `"indefinido"`.

---

# FASE 3 — 💰 El dibujo tiene que llegar al papel

Este es el hueco más grande frente a lo que el negocio necesita. Tu papá quiere una
simulación *para imprimirla y mostrársela al cliente*, y hoy `backend/ficha_pdf.py`
imprime un título, las advertencias normativas y una tabla de números. El cliente
recibe una tabla, no un dibujo de su escalera.

## 3.1 Alzado 2D acotado, en vectores, desde el backend

- [ ] `backend/ficha_dibujo.py`: consumir `dominio/geometria.py` y dibujar con el canvas
      de reportlab (`reportlab.graphics.shapes`) el alzado de la pieza a escala real,
      con líneas de cota, la medida escrita, y la escala indicada (1:20, 1:25).
- [ ] Incluir una **silueta humana de 1.70 m** al lado de la pieza, a la misma escala.
      No es decoración: es el detector de errores de captura más efectivo que existe.
      Si alguien escribió 320 en lugar de 3.20, la pieza sale veinte veces más alta que
      la persona y se ve de inmediato — antes de cortar el material.
- [ ] Vectores, no imagen rasterizada: se imprime nítido a cualquier tamaño y el archivo
      pesa una fracción.

## 3.2 Captura del 3D como apoyo

- [ ] En `frontend/src/components/Escalera3D.jsx`, agregar `preserveDrawingBuffer: true`
      al constructor del `WebGLRenderer`:

```js
const renderer = new THREE.WebGLRenderer({
  antialias: true,
  alpha: true,
  preserveDrawingBuffer: true,   // sin esto, toDataURL() sale en blanco
});
```

  **Este detalle cuesta una tarde de depuración si se descubre tarde.** Por defecto el
  navegador descarta el buffer de dibujo después de presentar el frame, así que
  `renderer.domElement.toDataURL()` devuelve una imagen vacía aunque en pantalla se vea
  perfecto. La bandera tiene un costo pequeño de rendimiento, irrelevante para esta escena.

- [ ] Enviar la captura al backend como base64 en el mismo POST que genera el PDF, y
      embeberla con `reportlab.platypus.Image`.
- [ ] Alternativa a considerar si la captura da problemas en móviles viejos: renderizar
      el 3D en el servidor. **No lo recomiendo** — implica un navegador headless en el
      contenedor, y el costo de infraestructura no se justifica frente a una captura del
      lado del cliente.

## 3.3 La ficha completa

La hoja que el cliente se lleva a su casa:

```
┌─────────────────────────────────────────┐
│  LOS MEJÍA          Cotización LM-...   │
│  Cliente · fecha · vigencia             │
├──────────────────────┬──────────────────┤
│                      │                  │
│   ALZADO 2D          │   VISTA 3D       │
│   con cotas          │   (captura)      │
│   y figura 1.70 m    │                  │
│                      │                  │
├──────────────────────┴──────────────────┤
│  Descripción · medidas · material       │
│  Desglose de precio                     │
│  TOTAL                                  │
├─────────────────────────────────────────┤
│  Advertencias normativas (si hay)       │
│  Vigencia · anticipo · qué no incluye   │
└─────────────────────────────────────────┘
```

- [ ] Un solo endpoint `POST /api/cotizaciones/<id>/ficha.pdf` que sirva para cualquier
      tipo de pieza, no uno por tipo. `escalera.py` hoy tiene su propio `/pdf` y `/excel`;
      unificarlos contra la especificación de la Fase 2.
- [ ] **Qué NO incluye** en letra visible: obra civil, resane, pintura de muro, energía
      eléctrica para el motor. La mitad de los pleitos en obra vienen de este párrafo
      faltante.
- [ ] Un QR en la esquina que abra la vista 3D interactiva en el teléfono del cliente.
      Barato de implementar, y es lo que la gente le enseña a su familia.

---

# FASE 4 — 💰 Cotización real de taller

## 4.1 Una cotización, muchas partidas

Hoy `Cotizacion` **es una sola pieza**: tiene `material`, `ancho_m`, `alto_m`. Pero un
cliente que está construyendo su casa no pide un portón: pide seis ventanas, un portón,
un barandal de escalera y dos protecciones. Eso es una cotización con cinco partidas,
un solo folio, un solo total y una sola vigencia.

Es la limitación estructural más costosa del modelo actual, porque hoy el dueño tiene
que crear cinco cotizaciones separadas y sumarlas a mano — y cuando el cliente negocia
un descuento sobre el total, no hay dónde ponerlo.

```python
class Cotizacion(db.Model):
    # se conservan: id, cliente_id, nombre_cliente, telefono, email, estado, creado_en
    folio = db.Column(db.String(20), unique=True, nullable=False)   # LM-2026-0001
    vigencia_hasta = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    tarifa_id = db.Column(db.Integer, db.ForeignKey("tarifas.id"))  # ver 4.2
    partidas = db.relationship("Partida", cascade="all, delete-orphan")


class Partida(db.Model):
    __tablename__ = "partidas"

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), nullable=False)
    tipo_trabajo_id = db.Column(db.Integer, db.ForeignKey("tipos_trabajo.id"), nullable=False)
    spec = db.Column(db.JSON, nullable=False)          # ← Fase 2
    descripcion = db.Column(db.String(200))
    cantidad = db.Column(db.Numeric(8, 2), nullable=False)   # m² o ml calculados
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    importe = db.Column(db.Numeric(12, 2), nullable=False)
    desglose = db.Column(db.JSON, nullable=False)      # ← ver 4.4
    orden = db.Column(db.Integer, default=0)
```

**Migración de datos:** cada `Cotizacion` existente se convierte en una cotización con
una sola partida. Es un script de una sola pasada; escribirlo con cuidado y probarlo
contra una copia de la base antes de correrlo en producción.

## 4.2 Precios versionados

Hoy `PrecioMaterial` tiene una fila por material y `seed.py` la **sobreescribe**. Eso
significa que cuando suba el acero, las cotizaciones del mes pasado pierden su explicación:
el total sigue guardado, pero ya no se puede reconstruir de dónde salió.

Además —y esto es un hallazgo importante— **no existe ninguna ruta para editar precios**.
Revisé todas las rutas registradas: `cotizador.py` solo expone un `GET /precios` público.
Hoy, cambiar el precio del acero exige editar `seed.py`, hacer commit, desplegar y correr
el seed. El dueño de una herrería no va a hacer eso, y por lo tanto los precios se van a
quedar viejos y el cotizador va a dejar de servir. **Esta es la razón número uno por la
que un cotizador se abandona a los tres meses.**

```python
class Tarifa(db.Model):
    """Un conjunto completo de precios con fecha de vigencia. Nunca se edita:
    se crea una nueva versión. Las cotizaciones apuntan a la que usaron."""
    __tablename__ = "tarifas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60))                # "Julio 2026"
    vigente_desde = db.Column(db.Date, nullable=False)
    activa = db.Column(db.Boolean, default=False)
    creada_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)


class PrecioTarifa(db.Model):
    __tablename__ = "precios_tarifa"

    id = db.Column(db.Integer, primary_key=True)
    tarifa_id = db.Column(db.Integer, db.ForeignKey("tarifas.id"), nullable=False)
    tipo_trabajo_id = db.Column(db.Integer, db.ForeignKey("tipos_trabajo.id"))
    concepto = db.Column(db.String(40), nullable=False)   # perfil, cristal, acabado, herraje, mano_obra
    clave = db.Column(db.String(40), nullable=False)      # ptr_1.5_cal14, templado_6mm...
    unidad = db.Column(db.String(6), nullable=False)      # m2, ml, pza, %
    precio = db.Column(db.Numeric(10, 2), nullable=False)
```

- [ ] `GET/POST/PUT /api/admin/tarifas` — pantalla de precios editable por el administrador. **Sin esto, nada de lo demás sirve a largo plazo.**
- [ ] Duplicar una tarifa vigente como punto de partida de la nueva ("Copiar Julio 2026
      a Agosto 2026 y subir todo 4 %"). Es cómo realmente se actualiza una lista de precios.
- [ ] Exportar e importar la tarifa como CSV. Un taller que ya lleva sus precios en Excel
      no va a teclear ochenta filas en un formulario.

## 4.3 Cómo se cobra cada sistema

El modelo actual cobra todo por m². Es correcto para herrería y **está mal para los otros
dos sistemas del negocio**:

| Sistema | Cómo se cobra en la realidad |
|---|---|
| **Herrería** | m² de superficie, ajustado por perfil y separación de barrotes |
| **Aluminio** | metros lineales de perfil **+** m² de cristal. Son dos precios que se mueven por separado: el perfil sigue al aluminio, el cristal al vidrio |
| **Cristal templado** | m² con **mínimo de fabricación**, más el canteado cobrado por perímetro, más barrenos por pieza |

La consecuencia práctica de no modelarlo: **una ventana de 40 × 40 cm no cuesta la sexta
parte de una de 1 × 1 m.** El templado tiene un mínimo por pieza y el canteado se paga por
perímetro, no por área. Con el modelo actual el taller pierde dinero en cada pieza chica
y lo pierde sin darse cuenta, que es la peor forma de perderlo.

- [ ] `dominio/precios.py` con una estrategia por sistema, no un solo `if`.
- [ ] Para aluminio: calcular metros lineales de perfil desde la geometría (perímetro +
      divisiones), no pedírselos al usuario. El dato ya está en la especificación.

## 4.4 El desglose y la simulación del dueño

Lo que originalmente se pidió: que el dueño pueda tomar las medidas del cliente y hacer
la simulación. Hoy eso no existe — el administrador solo puede aprobar o rechazar, y
`precio_estimado` se escribe una vez al recibir la solicitud y nunca se puede recalcular.

- [ ] `POST /api/admin/cotizaciones/<id>/simular` — recalcula con parámetros que el dueño
      ajusta en vivo, **sin guardar** hasta que él confirme.
- [ ] Guardar el `desglose` completo en JSON en cada partida, para que la cotización sea
      reproducible y auditable meses después:

```json
{
  "cantidad": 7.68, "unidad": "m2", "precio_unitario": 3100,
  "material_base": 23808, "ajuste_separacion": 1734,
  "acabado": 3686, "herrajes": 10650,
  "merma_pct": 7, "merma": 2044,
  "mano_obra": 2458, "flete": 176,
  "costo_directo": 44556, "utilidad_pct": 25, "utilidad": 11139,
  "subtotal": 55695, "iva": 8911, "total": 64606,
  "tarifa_id": 3, "spec_version": 1
}
```

- [ ] Parámetros que el dueño debe poder mover en la simulación: precio unitario,
      mano de obra por m², flete por km y kilómetros, merma %, utilidad %, descuento,
      IVA sí/no.
- [ ] Mostrarle **el margen sobre venta**, no el porcentaje de utilidad sobre costo.
      Son números distintos y el segundo engaña: 25 % sobre costo es 20 % sobre venta.
      Un dueño que confunde los dos cree que gana más de lo que gana.
- [ ] Que el estimado del cliente se presente siempre como **rango** (±10 %) y con la
      leyenda de que está sujeto a medición en sitio. Un número exacto en la web se
      vuelve una promesa, y las medidas del cliente casi nunca son las reales.

---

# FASE 5 — 💰 Lo que el taller necesita en la mano

Esta fase es la que convierte el sistema de "página web bonita" a "herramienta que se usa
todos los días". Y sale casi gratis de la Fase 2: el modelo paramétrico ya tiene la
geometría, solo hay que recorrerla y contar.

## 5.1 Lista de corte (despiece)

- [ ] `dominio/despiece.py`: de la especificación, sacar cuántos tramos de cada perfil,
      de qué largo, y en qué ángulo van cortados.
- [ ] Optimización de corte de primer orden: acomodar los tramos requeridos en barras
      comerciales de 6 metros minimizando el sobrante. El algoritmo *first-fit decreasing*
      es diez líneas y resuelve el 90 % del beneficio; no hace falta un solver.
- [ ] Reportar **merma real calculada** contra el porcentaje teórico que se cobró. Si el
      taller cobra 7 % de merma y realmente desperdicia 14 %, está perdiendo dinero en
      cada trabajo y hoy no hay forma de saberlo.
- [ ] PDF de orden de trabajo para el trabajador: dibujo, lista de corte, herrajes,
      y el número de folio. Sin precios — el trabajador no necesita verlos y el cliente
      no debe verlos si la hoja se queda en la obra.

## 5.2 Requisición de material

- [ ] Sumar el material de todos los proyectos activos y generar una lista de compra:
      cuántas barras de PTR de cada calibre, cuántos m² de cristal, cuántos herrajes.
      Es la diferencia entre ir al proveedor tres veces por semana y una.

---

# FASE 6 — 3D paramétrico para el resto del catálogo

`Escalera3D.jsx` (233 líneas de three.js puro) demuestra que la capacidad ya está en el
proyecto. El problema es que **solo existe para escaleras**, que es el producto más
complejo de modelar y probablemente no el más vendido.

Ventanas, canceles, portones y rejas son geométricamente mucho más simples: un marco,
divisiones y paneles. Con lo que ya está resuelto, esto es trabajo de días.

- [ ] `frontend/src/components/Pieza3D.jsx` — un componente genérico que recibe la
      especificación y arma la escena. Un constructor por `modo_dibujo`, igual al patrón
      de `CONSTRUCTORES[tipo]` que ya usa `Escalera3D.jsx`.
- [ ] `frontend/src/components/Pieza2D.jsx` — el alzado acotado en SVG, que es lo que
      realmente sirve para confirmar medidas. Debe compartir la lógica de geometría con
      el 2D del PDF; si el dibujo de la pantalla y el del papel no coinciden, se pierde
      la confianza en los dos.
- [ ] Ambos consumen la misma especificación de la Fase 2. Nada de un formato para el 3D
      y otro para el precio.
- [ ] Detalles de implementación que valen la pena: cristal con transparencia real y
      cotas visibles también en 3D. Zoom con la rueda del ratón y gesto de pinza —
      `Escalera3D.jsx` hoy solo rota, y en un teléfono la gente intenta hacer pinza por instinto.
- [ ] Cuidar la limpieza de recursos: `renderer.dispose()` y liberar geometrías y
      materiales al desmontar. Con varias piezas en pantalla, las fugas de memoria de
      WebGL tumban el navegador en teléfonos de gama media.

---

# FASE 7 — 💰 Operación del taller

Funcionalidad nueva, ordenada por relación entre valor y esfuerzo. Nada de esto es
imprescindible para que el sistema funcione; todo esto es lo que hace que se use.

## 7.1 Aceptación de la cotización por el cliente

- [ ] Link público con token firmado: `/cotizacion/<token>`. El cliente ve su ficha con
      el dibujo y un botón de "Acepto esta cotización".
- [ ] Guardar fecha, hora e IP de la aceptación. No es un contrato ante notario, pero es
      infinitamente mejor que "usted me dijo que sí por teléfono".
- [ ] Reutilizar `itsdangerous`, que ya está en el proyecto para los tokens de sesión.
      No hace falta nada nuevo.

## 7.2 Anticipos y estado de cuenta

Las herrerías viven del anticipo: 50 % para comprar material, 50 % contra entrega. Es
central a la operación y no está modelado en ninguna parte.

- [ ] Tabla `Pago(proyecto_id, monto, metodo, fecha, comprobante_url, registrado_por)`.
- [ ] Que el panel del cliente muestre cuánto lleva pagado y cuánto resta.
- [ ] Que ningún proyecto pueda pasar a "en proceso" sin anticipo registrado. Esa regla
      de negocio, sola, evita el problema más caro de un taller chico: comprar material
      para un trabajo que se cayó.
- [ ] **No** integrar pasarela de pagos todavía. Ver la sección "Lo que no recomiendo".

## 7.3 Seguimiento con fotos

- [ ] Que el trabajador suba fotos de avance desde el teléfono, y que el cliente las vea
      en su panel. La infraestructura de subida de imágenes ya existe en
      `routes/admin.py`; es reutilizarla.
- [ ] Comprimir del lado del cliente antes de subir (`canvas.toBlob` con calidad 0.7).
      Una foto de teléfono moderno pesa 4 MB y en la obra hay señal de 3G.
- [ ] Esto es lo que más reduce las llamadas de "¿cómo va mi portón?", que es tiempo del
      dueño convertido en tiempo de taller.

## 7.4 Vigencia, seguimiento y recordatorios

- [ ] Expirar cotizaciones automáticamente a los 30 días (estado `vencida`) y permitir
      revivirlas recalculando con la tarifa actual. Una cotización de hace cuatro meses
      con precios de hace cuatro meses es una pérdida garantizada.
- [ ] Tablero de seguimiento: cotizaciones sin respuesta a 3, 7 y 15 días. **La mayoría
      de las cotizaciones no se pierden por precio, se pierden por falta de seguimiento.**
- [ ] Link `wa.me` prellenado con el resumen y el enlace al PDF. Es un `<a href>`,
      no una integración: `https://wa.me/52<tel>?text=<mensaje codificado>`.

## 7.5 Agenda y capacidad

- [ ] Calendario de instalaciones con la capacidad semanal del taller (en m² o en jornadas).
- [ ] Avisar cuando la semana ya está comprometida. Prometer entregas que no se pueden
      cumplir es la forma más rápida de perder la reputación en un negocio que vive de
      recomendaciones.
- [ ] Fecha estimada de entrega calculada a partir de la carga real, no del optimismo.
      `Proyecto` ya tiene `fecha_estimada_entrega`; hoy nadie la calcula.

## 7.6 Bitácora de auditoría

- [ ] Tabla `Bitacora(usuario_id, entidad, entidad_id, accion, antes, despues, creado_en)`
      para cambios de precio, de estado y de asignación.
- [ ] Con tres roles y varias personas tocando los mismos registros, "¿quién le bajó el
      precio a esta cotización?" es una pregunta que se va a hacer. Conviene que tenga
      respuesta.

---

# FASE 8 — Los números del negocio

Lo que le dice a tu papá si sus precios están bien. Todo lo anterior recopila datos;
esta fase los usa.

- [ ] **Costo estimado contra costo real** por proyecto: material comprado y horas
      trabajadas contra lo cotizado. Es el único reporte que realmente importa.
      Después de veinte trabajos, revela qué tipo de pieza deja dinero y cuál se cotiza
      por debajo del costo.
- [ ] **Tasa de conversión** por tipo de trabajo y por rango de precio. Si el 90 % de los
      portones se aprueban y el 20 % de los canceles, hay algo que corregir en el precio
      del cancel — o en cómo se presenta.
- [ ] **Horas por m²** registradas por el trabajador, para calibrar la mano de obra con
      datos en vez de con corazonada. Hoy `320 $/m²` es un número inventado; con dos
      meses de registro deja de serlo.
- [ ] Exportar todo a Excel. El contador lo va a pedir y `XlsxWriter` ya está instalado.

---

# Backlog — buenas ideas, no todavía

Cosas que valen la pena y que no deben distraer de las fases anteriores:

- **PWA offline para el trabajador.** En obra no hay señal. Que la app cargue y permita
  registrar avance para sincronizar después. Buen valor, pero pesa: manejo de conflictos
  y estado local. Después de la Fase 7.3.
- **Plantillas de piezas frecuentes.** "Ventana estándar 1.20 × 1.00 en aluminio serie 2"
  como punto de partida en un clic. Barato y muy usado; se puede colar en cualquier fase.
- **Comparador de opciones para el cliente.** La misma pieza en cal. 18 y cal. 14, lado a
  lado con los dos precios. Vende el material más caro mejor que cualquier argumento.
- **Firma en pantalla** del cliente al aceptar (canvas). Bonito, marginal sobre 7.1.
- **Multi-taller / multi-sucursal.** Solo si el negocio crece a otra ubicación.
  Diseñarlo antes es adivinar.
- **Búsqueda de cotizaciones por cliente, teléfono o folio.** Necesario a partir de unos
  cientos de registros; trivial de agregar cuando duela.

---

# Lo que NO recomiendo hacer

Después de veinte años, la lista de lo que no se debe construir es más valiosa que la de
lo que sí. Estas son las tentaciones concretas de este proyecto:

**No reescribir a Next.js, TypeScript ni cambiar de framework.** El stack actual —Flask
con React y Vite— es adecuado, está desplegado y funciona. Una reescritura consumiría
meses y no le daría al taller una sola función nueva. TypeScript se puede introducir
gradualmente, archivo por archivo, si algún día se justifica.

**No construir un CAD ni importar DXF de arquitectos.** Es la tentación más grande de un
proyecto así y es un pozo sin fondo. El modelo paramétrico de la Fase 2 cubre el 95 % de
lo que fabrica una herrería. El 5 % restante se dibuja a mano, como siempre.

**No microservicios, ni Docker Compose elaborado, ni Kubernetes.** Dos servicios en
Railway con una base de datos es la arquitectura correcta para este tamaño, y lo va a
seguir siendo con veinte veces más uso.

**No app móvil nativa.** Una PWA cubre lo que se necesita sin tiendas de aplicaciones,
sin dos bases de código y sin procesos de revisión.

**No la API de WhatsApp Business.** Requiere verificación de negocio, tiene costo por
mensaje y complejidad de plantillas. Los links `wa.me` dan el 80 % del beneficio por
cero pesos y cero trámites.

**No pasarela de pagos en línea al inicio.** Los anticipos de una herrería se pagan por
transferencia o en efectivo. Registrar el pago es lo que falta; cobrarlo en línea es
resolver un problema que el taller no tiene.

**No convertirlo en SaaS para otras herrerías todavía.** Es un buen negocio potencial y
una distracción segura. Que el taller de tu papá lo use tres meses completos; los
problemas reales que aparezcan en ese tiempo son los que definen si el producto sirve
para alguien más. Diseñar para multi-tenant desde ahora es pagar complejidad por un
cliente hipotético.

**No IA generativa para diseñar piezas.** El chatbot de atención tiene sentido y ya está.
Generar diseños con IA suena impresionante y produce piezas que no se pueden fabricar
con el material que hay en el taller.

---

# Riesgos y decisiones abiertas

| Riesgo | Mitigación |
|---|---|
| La migración de `Cotizacion` a partidas toca datos reales | Escribir el script, correrlo contra una copia de la base, verificar totales antes y después, y solo entonces en producción |
| Los precios inventados en `seed.py` se quedan como "los precios" | Bloquear la salida a producción hasta que el dueño capture su tarifa real (Fase 4.2) |
| El disco de Railway es efímero | Volume montado, ya documentado en el README. Verificar que esté configurado, no solo documentado |
| El identificador del modelo del chatbot está fijo en el código | Moverlo a variable de entorno y confirmar en la documentación de Anthropic que la versión siga vigente |
| La especificación de pieza cambia de forma | El campo `version` desde la primera línea de código, y una función de migración por versión |
| Alcance creciendo sin fin | Este documento. Si algo no está aquí, se discute antes de escribirse |

**Decisiones que hay que tomar con tu papá antes de empezar:**

1. ¿El cliente ve un precio en la web, o solo manda solicitud y el precio llega después?
   Cambia el diseño de la Fase 4. Mi recomendación: rango, nunca número exacto.
2. ¿Se factura con IVA a todos los clientes, o solo a quien pide factura?
3. ¿Cuántos trabajadores van a usar el sistema de verdad? Si es uno, la Fase 7.5 sobra.
4. ¿Hay una lista de precios real en papel o en Excel? Si existe, la Fase 4.2 empieza
   por importarla, no por capturarla.

---

# Orden de ejecución sugerido

```
Semana 1     Fase 0 completa · Fase 1.1 (Alembic) · Fase 1.4 (cambio de contraseña)
Semana 2-3   Fase 2 completa  ← la que desbloquea todo
Semana 4     Fase 3 (dibujo 2D en el PDF)
Semana 5-6   Fase 4 (partidas y tarifas versionadas)
Semana 7     Fase 5.1 (lista de corte)
Semana 8-9   Fase 6 (3D paramétrico)
Después      Fase 7 por prioridad del taller · Fase 8 cuando haya datos
```

**Si solo hubiera tiempo para tres cosas:** Fase 0 (seguridad), Fase 3 (que el dibujo
llegue al papel) y Fase 4.2 (que el dueño pueda cambiar los precios él mismo).

Esas tres, en ese orden, son la diferencia entre un proyecto que se usa y uno que se
abandona.
