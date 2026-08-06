# Herrería Los Mejía — Estado de la versión y checklist de pruebas

**Fecha:** 31 de julio de 2026
**Rama:** `main` (fusionada desde `fase-0/seguridad`)
**Sitio:** https://herreria-los-mejia-production.up.railway.app/

Este documento resume qué incluye la versión actual (las 8 fases de
`actualizar.md`, backend y frontend) y trae un checklist para probar cada
cosa a mano, sección por sección.

---

## 1. Qué incluye esta versión

### Seguridad y cimientos (Fase 0–1)
- Sin contraseñas de prueba en el repo; `SECRET_KEY` obligatoria en producción.
- Chatbot limitado (20 peticiones/hora por IP) y validado.
- Migraciones con Alembic (ya no se pierde el historial de la base al cambiar el esquema).
- Validación de datos y manejo de errores en todo el backend.
- Cambio de contraseña propio y revocación de sesión (`token_version`).
- Logging a stdout, script de respaldo, límite de tamaño de subida (8 MB).

### Cotizador (Fase 2–4)
- Cada pieza tiene una especificación unificada (`spec`) de la que salen el
  dibujo, el precio y (a futuro) el despiece.
- Catálogo de 9 tipos de trabajo (portón corredizo, abatible, reja, protección,
  barandal, cancelería, ventana de aluminio, puerta de cristal templado, escalera).
- **Tarifas de precios versionadas**, editables desde el panel — ya no hay que
  tocar código para cambiar un precio.
- El cotizador público deja **agregar varias piezas** en una sola solicitud
  ("+ Agregar otra pieza"). El precio mostrado siempre es un **rango ±10 %**,
  nunca un número exacto.
- Cada sistema se cobra distinto: herrería por m², aluminio por perfil (ml) +
  cristal (m²), cristal templado con mínimo de fabricación + canteado por
  perímetro.
- El administrador puede **simular** una cotización (ajustar mano de obra,
  flete, merma, utilidad) sin guardar nada, y ver el margen sobre venta.

### Ficha y dibujo (Fase 3, 6)
- La ficha de escalera en PDF trae un alzado 2D acotado con una silueta
  humana de 1.70 m de referencia, más la captura del 3D.
- Vista previa en 3D y 2D del resto del catálogo (portones, ventanas, etc.)
  directo en el cotizador público, mientras se llenan las medidas.

### Taller (Fase 5)
- Lista de corte automática por partida, con la merma real calculada contra
  la que se cobró.
- PDF de orden de trabajo para el taller (sin precios).
- Requisición de material: cuántas barras de 6 m hacen falta en total entre
  todos los proyectos activos.

### Operación (Fase 7)
- Link público para que el cliente acepte su cotización
  (`/cotizacion/<token>`), sin necesidad de cuenta.
- Registro de anticipos y pagos — un proyecto no puede pasar a "en proceso"
  sin al menos un pago registrado.
- El trabajador sube fotos de avance desde su panel; el cliente las ve en el suyo.
- Cotizaciones vencidas se marcan solas (script programable) y se pueden
  revivir recalculando con la tarifa vigente.
- Tablero de seguimiento (3/7/15 días sin respuesta) con link directo a WhatsApp.
- Agenda de capacidad semanal del taller.
- Bitácora: quién cambió qué precio, estado o asignación, y cuándo.

### Números del negocio (Fase 8)
- El trabajador registra sus horas por proyecto.
- El administrador captura el costo real de material al conciliar.
- Reportes: costo real contra cotizado (con margen), tasa de conversión por
  tipo de trabajo y por rango de precio, horas por m².
- Todo exportable a un solo archivo de Excel.

---

## 2. Cuentas de prueba en producción

| Rol | Correo |
|---|---|
| Administrador | `admin@losmejia.com` |
| Administrador | `ramon@losmejia.com` |
| Trabajador | `trabajador@losmejia.com` |
| Trabajador | `obed@losmejia.com` |
| Cliente | `cliente@losmejia.com` |
| Cliente | `juangonza@live.com.mx` |

Las contraseñas no van en este archivo — son las que ya tienes.

---

## 3. Checklist de pruebas manuales

Márcalas conforme las vayas probando en el sitio real. Si algo no se
comporta como dice aquí, es un bug — anótalo con el paso exacto para
reportarlo.

### A. Sitio público (sin iniciar sesión)

- [ ] Entrar a la portada, ver el catálogo y las secciones normales del sitio.
- [ ] Ir a "Cotizador" → pestaña "Propuesta personalizada".
- [ ] Elegir un material, poner ancho y alto → debe aparecer un **rango de
      precio** (no un número exacto), la **vista 3D** y el **alzado 2D** al
      lado, actualizándose en vivo.
- [ ] En la vista 3D: arrastrar para rotar, usar la rueda del mouse (o pinza
      en celular) para hacer zoom.
- [ ] Click en "+ Agregar otra pieza" → aparece un renglón nuevo con
      material/ancho/alto/piezas. Agregar 2 o 3 piezas distintas.
- [ ] Click en "Solicitar cotización formal" → llenar nombre y teléfono →
      enviar.
- [ ] Debe confirmar el envío y mostrar un **folio** y un rango de precio total.
- [ ] Repetir sin ninguna pieza adicional (una sola pieza) y confirmar que
      también funciona igual que antes.
- [ ] Probar la pestaña "Modelo del catálogo": elegir un modelo existente,
      ver que el precio se calcule, y enviar la solicitud.

### B. Aceptación pública de cotización

- [ ] Iniciar sesión como administrador → pestaña "Cotizaciones" → click en
      "Copiar link de aceptación" de alguna cotización.
- [ ] Abrir ese link en una ventana privada/incógnito (sin sesión).
- [ ] Debe mostrar el folio, las piezas, el total, y el botón
      "Acepto esta cotización".
- [ ] Click en aceptar → debe confirmar la aceptación con fecha y hora.
- [ ] Volver a entrar al mismo link → ya no debe dejar aceptar de nuevo
      (debe decir que ya fue aceptada).

### C. Panel de cliente

- [ ] Iniciar sesión con una cuenta de cliente.
- [ ] Ver "Mis cotizaciones" y "Mis proyectos".
- [ ] En un proyecto aprobado, si el trabajador ya subió fotos, debe
      aparecer "Ver fotos de avance (N)" — al abrirlo, ver las imágenes.
- [ ] Debe verse el saldo pendiente (o "Pagado completo" si ya no debe nada).

### D. Panel de trabajador

- [ ] Iniciar sesión con una cuenta de trabajador.
- [ ] Ver "Mis proyectos asignados" y la "Cola general pendiente".
- [ ] En un proyecto asignado, click en "Registrar horas / subir foto".
- [ ] Registrar unas horas (ej. 4) con una nota → debe confirmar y sumarse
      al total mostrado.
- [ ] Subir una foto (jpg/png) → debe aparecer en la galería de ese proyecto.
- [ ] Intentar cambiar el estado a "En proceso" en un proyecto **sin ningún
      pago registrado** → debe **rechazarlo** con un mensaje claro.
- [ ] Pedirle al administrador que registre un pago para ese proyecto (ver
      sección E) y repetir — ahora sí debe dejar pasar a "En proceso".

### E. Panel de administrador

**Pestaña Pedidos**
- [ ] Ver la lista de proyectos, filtrar por estado.
- [ ] Abrir "Ver detalle" de un proyecto con partidas.
- [ ] Click en "Ver lista de corte" de una partida → debe mostrar cuántas
      barras de 6 m y el % de merma real vs. teórica.
- [ ] Click en "Descargar orden de trabajo (PDF)" → debe bajar un PDF sin precios.
- [ ] Registrar un pago (monto + método) → debe actualizar el saldo al instante.
- [ ] Capturar el "costo real de material" → guardar.
- [ ] Ver la galería de fotos que subió el trabajador.

**Pestaña Cotizaciones**
- [ ] Si hay cotizaciones sin respuesta (3+ días), debe aparecer el aviso de
      seguimiento arriba — expandirlo y ver el detalle por antigüedad.
- [ ] Click en "Simular" en una cotización → ajustar mano de obra, flete,
      merma, utilidad, IVA → click en "Recalcular" → debe mostrar costo
      directo, utilidad, **margen sobre venta**, subtotal, IVA, total y el
      rango estimado al cliente. Confirmar que **no cambia nada guardado**
      (recargar la página y ver que el total de la cotización sigue igual).
- [ ] Click en "WhatsApp" de una cotización con teléfono → debe abrir
      `wa.me` con un mensaje prellenado.
- [ ] Si hay una cotización vencida, debe aparecer el botón "Revivir con
      precios actuales" → probarlo y confirmar que le pone vigencia nueva.
- [ ] Aprobar una cotización nueva (con o sin trabajador asignado) → debe
      crear el proyecto y aparecer en Pedidos con una fecha estimada de entrega.

**Pestaña Catálogo**
- [ ] Subir/editar un producto con imagen — esto no cambió, pero confirma
      que sigue funcionando.

**Pestaña Tarifas**
- [ ] Ver la tarifa activa (marcada "ACTIVA").
- [ ] Editar un precio existente y guardar → debe confirmar.
- [ ] Crear una tarifa nueva vacía, agregar un precio, y activarla.
- [ ] Probar "Duplicar…" sobre una tarifa, con un ajuste de +4 %, y
      confirmar que los precios de la copia salen 4 % más altos.

**Pestaña Requisición**
- [ ] Debe mostrar el total de barras de 6 m necesarias entre todos los
      proyectos activos, y el detalle por partida.

**Pestaña Agenda**
- [ ] Debe mostrar las semanas con proyectos activos, la carga contra la
      capacidad, y marcar en rojo si alguna semana está sobrecargada.

**Pestaña Reportes**
- [ ] Ver las 4 tablas: costo real vs. cotizado, conversión por tipo,
      conversión por rango de precio, horas por m².
- [ ] Click en "Descargar todo en Excel" → debe bajar un `.xlsx` con las 4 hojas.

**Pestaña Bitácora**
- [ ] Debe listar los cambios recientes (precios, estados, asignaciones)
      con quién los hizo y cuándo.
- [ ] Probar el filtro por tipo de entidad (tarifa, proyecto, cotización).

**Pestaña Equipo**
- [ ] Crear una cuenta de trabajador nueva — esto no cambió, confirma que sigue igual.

**Pestaña Escalera**
- [ ] Calcular una escalera, ver el 3D (ahora con zoom de rueda/pinza),
      descargar el PDF (debe traer el alzado 2D con la silueta humana) y el Excel.

---

## 4. Si algo falla

Anota: la pestaña donde pasó, qué esperabas ver, qué viste en realidad, y
si hay un mensaje de error en pantalla (o en la consola del navegador,
tecla F12 → pestaña "Console"). Con eso es mucho más rápido corregirlo.
