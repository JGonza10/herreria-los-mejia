# Manual del Sistema Herrería Los Mejía

_Manual de usuario del sitio y sistema de gestión de Herrería Los Mejía. Refleja el estado del código al 2026-09-08. Regenera los formatos imprimibles con `python generar_manual.py`._

## 1. Qué es

Sitio web y sistema de gestión para un taller que trabaja hierro, aluminio y vidrio: portones, rejas, barandales, ventanas, cancelería y escaleras. El objetivo central, el que decide cómo está armado todo: que el dueño del taller pueda tomar las medidas que da un cliente, simular la cotización, y mostrarle al cliente el resultado.

Hay tres tipos de cuenta: **cliente**, **trabajador** y **administrador**. Cada uno entra por el mismo `/login` y ve un panel distinto según su rol.

## 2. El sitio público (sin cuenta)

Cualquier visitante, sin registrarse, puede:

- Ver el **catálogo de productos** del taller, filtrable por material (hierro, aluminio, vidrio).
- Usar el **cotizador**: elegir material y capturar ancho y alto (siempre en metros) para obtener un precio estimado al instante.
- Usar el **chatbot de atención**, que responde dudas sobre materiales y tiempos, y guía a usar el cotizador si se quiere un precio — no da precios exactos por su cuenta, esos siempre salen del cotizador.
- **Solicitar una cotización formal**, dejando nombre y teléfono — no hace falta tener cuenta para pedirla.
- Si recibiste el enlace de una cotización (por WhatsApp o donde te la haya compartido el taller), puedes **verla y aceptarla** desde ese enlace sin necesidad de iniciar sesión.

## 3. Cuenta de cliente

Al registrarte (correo y contraseña) tienes acceso a tu propio panel:

- **Mis cotizaciones**: todas las que has solicitado, con su estado.
- **Mis proyectos**: los pedidos que ya se aprobaron y están en curso, con el avance en porcentaje, las fotos que suba el trabajador, y cuánto llevas pagado y cuánto resta.

## 4. Cuenta de trabajador

El panel del trabajador muestra:

- **Mis proyectos asignados** y los **proyectos pendientes** sin asignar todavía, para ver qué hay en la cola general.
- Actualizar el **avance** de un proyecto propio y cambiar su estado (a "en proceso" o "terminado") — una regla de negocio impide pasar un proyecto a "en proceso" si todavía no tiene ningún anticipo registrado.
- **Subir fotos de avance** desde el teléfono, visibles después en el panel del cliente.
- **Registrar horas trabajadas** en un proyecto, con fecha y notas.
- La **calculadora de escaleras** (ver sección 6) también está disponible para el trabajador, no solo para el administrador.

## 5. Panel de administrador

El panel tiene estas pestañas:

| Pestaña | Para qué |
|---|---|
| Pedidos | Los proyectos en curso: asignar trabajador, cambiar estado, capturar avance, registrar anticipos y pagos, y anotar el costo real de material al conciliar un proyecto. |
| Cotizaciones | Todas las solicitudes: aprobar (genera el proyecto automáticamente, con fecha estimada de entrega calculada según la carga de trabajo actual del taller) o rechazar. Cada cotización trae también un enlace de WhatsApp ya redactado para mandársela al cliente. Una vista de **seguimiento** agrupa las que llevan 3, 7 o 15+ días sin respuesta, y las que ya vencieron se pueden **revivir** recalculando con los precios vigentes. |
| Catálogo | Alta, edición y baja de productos del catálogo público, con imagen. |
| Tarifas | Listas de precios con fecha de vigencia. Solo una puede estar activa a la vez; nunca se edita una tarifa vieja, se crea una nueva versión — así una cotización de hace meses sigue siendo reconstruible con los precios que tenía cuando se hizo. Se puede duplicar una tarifa existente aplicando un ajuste porcentual parejo, en vez de capturar todo de nuevo. |
| Requisición | Suma el material de todos los proyectos activos (cuántas barras de 6 metros hacen falta en total), para comprar una sola vez en vez de varias veces por semana. |
| Agenda | Qué tan comprometida está la capacidad semanal del taller, con aviso si una semana ya está sobrecargada. |
| Reportes | Costo estimado contra costo real por proyecto, tasa de conversión de cotizaciones (por tipo de trabajo y por rango de precio) y horas trabajadas por metro cuadrado — todo también exportable a Excel. |
| Bitácora | Registro de quién cambió qué (precios, estados de proyecto, asignaciones) y cuándo. |
| Equipo | Alta de cuentas de trabajador o administrador, y restablecer la contraseña de alguien del equipo (no hay recuperación por correo: la reinicia el administrador). |
| Escalera | La calculadora de escaleras (ver sección 6), también disponible aquí. |

Además, desde una cotización se puede generar una **simulación de precio en vivo**: el administrador ajusta mano de obra, flete, merma y utilidad y ve el total recalculado al momento, sin que se guarde nada hasta confirmarlo — y ve el margen sobre venta, no solo el porcentaje de utilidad sobre costo, que es un número distinto y más fácil de malinterpretar.

## 6. Calculadora de escaleras

Herramienta especializada (administrador y trabajador) que calcula escalones, huella, contrahuella, inclinación y espacio requerido para cuatro tipos de escalera: recta, en L, en U y de caracol. Valida el resultado contra el Reglamento de Construcciones de CDMX y la Ley de Blondel, avisando si algo queda fuera de norma (huella muy angosta, tramo sin descanso, escalera de caracol usada como principal, etc.). El resultado se puede descargar como PDF (con la vista 3D si se capturó) o como Excel.

**Esto es una calculadora de apoyo para cotizar y fabricar, no un cálculo estructural certificado** — si un proyecto cae bajo un reglamento distinto al de CDMX, hay que confirmarlo aparte.

## 7. Lista de corte y orden de trabajo

Para piezas con barrotes (portones, rejas, protecciones), el sistema puede calcular cuántos tramos de perfil hacen falta y cómo acomodarlos en barras comerciales de 6 metros, minimizando el sobrante. A partir de ahí se genera un PDF de **orden de trabajo** para el taller, sin precios — el trabajador no necesita verlos y no debe verlos si la hoja se queda en obra.

## 8. Instalación y arranque

```bash
# Backend — sin DATABASE_URL cae a SQLite, no hace falta PostgreSQL local
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py                   # http://localhost:5000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

`backend/.env` (nunca se sube al repositorio): `SECRET_KEY`, `ANTHROPIC_API_KEY` (para el chatbot), `FRONTEND_ORIGIN`, `PORT`. En producción corre como dos servicios separados en Railway (backend y frontend) con una base PostgreSQL.

## 9. Lo que todavía no hace

- **No hay migraciones de base de datos formales (Alembic)**: el esquema se crea solo al arrancar, pero agregar una columna nueva a una tabla que ya existe en producción no se aplica sola — hay que tenerlo presente antes de cualquier cambio de estructura.
- **El disco donde se guardan las fotos de productos y de avance es efímero en Railway**: si no hay un volumen de almacenamiento montado, esas imágenes se pueden perder en cada despliegue nuevo.
- **No se puede cerrar sesión de forma forzada a distancia**: los tokens de acceso duran 30 días y no se pueden revocar uno por uno; solo cambiar la contraseña de esa cuenta invalida sus sesiones abiertas.
- **No hay recuperación de contraseña por correo**: para un cliente, no está resuelta (tendría que pedirle al taller que le ayude); para trabajador o administrador, la restablece otro administrador desde la pestaña Equipo. Es una decisión deliberada para un taller chico, no un pendiente técnico.
- **El chatbot depende de una API externa de pago** (Anthropic) con la llave del propio taller — tiene límite de peticiones para evitar abuso, pero si la llave no está configurada en el servidor, el chatbot simplemente avisa que no está disponible en vez de fallar.
- **No hay pasarela de pagos en línea ni facturación electrónica (CFDI)**: los anticipos y pagos se registran a mano en el sistema después de recibirse por transferencia o efectivo; no se cobran desde la web.
- **No existe una app móvil nativa** — el sistema está pensado para usarse desde el navegador del teléfono en el taller y en obra.
- **El modelo 3D solo existe para escaleras** por ahora; el resto del catálogo (ventanas, portones, rejas, cancelería) todavía no tiene su propia vista 3D ni un alzado 2D acotado listo para imprimir junto al precio.
