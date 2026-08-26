# SastreArte

Aplicación web para gestionar clientes, pedidos, asignaciones, pagos, insumos, listas de compra y trabajadores de una sastrería.

La interfaz utiliza el logo de SastreArte de los informes y un diseño propio de sastrería, adaptable a escritorio, tablet y celular. No se incluye una aplicación móvil nativa.

## Puesta en marcha con Docker

1. Abre una terminal.

2. Entra a la carpeta del proyecto:

   ```bash
   cd SastreArte
   ```

3. Crea el archivo de configuración:

   En macOS o Linux:

   ```bash
   cp .env.example .env
   ```

   En Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Construye e inicia todo:

   ```bash
   docker compose up --build
   ```

5. Abre la aplicación en [http://localhost:5173](http://localhost:5173).

6. La API está disponible en [http://localhost:8000/api/salud](http://localhost:8000/api/salud).

7. Ejecuta las pruebas en otra terminal:

   ```bash
   docker compose exec backend pytest
   ```

8. Para detener el sistema:

   ```bash
   docker compose down
   ```

Si necesitas borrar el volumen local y reconstruir la base desde cero, usa `docker compose down -v`. Esto elimina los datos guardados en PostgreSQL.

## Estructura

```text
SastreArte/
├── backend/        API Flask, servicios, repositorios y pruebas
├── frontend/       React, TypeScript, HTML y CSS
├── postgresql/     Esquema oficial y datos iniciales
├── docker-compose.yml
└── README.md
```

Servicios y puertos:

| Servicio | Puerto | Función |
|---|---:|---|
| `frontend` | 5173 | Interfaz web |
| `backend` | 8000 | API REST en Python/Flask |
| `postgresql` | 5432 | Base de datos PostgreSQL 16 |

## Arquitectura

El backend respeta la separación en capas del modelo MVC del análisis:

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Controlador | `backend/rutas/` | HTTP: rutas, códigos de estado, control de rol. No contiene reglas ni SQL. |
| Modelo (negocio) | `backend/servicios/` | Validaciones, dominios válidos y cálculos como el IVA. |
| Modelo (persistencia) | `backend/repositorios/` | Únicamente SQL parametrizado contra PostgreSQL. |
| Vista | `frontend/src/` | React + TypeScript; sólo consume la API. |

Ninguna ruta llama directamente a un repositorio: siempre pasa por un servicio.

## Reglas de negocio

**Dominios cerrados.** Los valida `backend/servicios/pedidos.py`, los replica la
base con restricciones `CHECK` y los expone `GET /api/pedidos/opciones`, que es
la fuente que consume el frontend.

| Campo | Valores admitidos |
|---|---|
| `estado` | `PENDIENTE`, `EN_PROCESO`, `LISTO_PARA_ENTREGA`, `ENTREGADO`, `CANCELADO` |
| `prioridad` | `BAJA`, `MEDIA`, `ALTA`, `URGENTE` |
| `complejidad` | `BAJA`, `MEDIA`, `ALTA` |
| `unidad_medida` | `MM`, `CM`, `METROS`, `UNIDADES` |

`UNIDADES` cubre lo que se cuenta de a uno —botones, cierres, conos de hilo— y
no se mide en largo. Las unidades las expone `GET /api/insumos/opciones`.

La entrada se normaliza a mayúsculas con guion bajo, de modo que `en proceso`
y `EN_PROCESO` no queden como dos estados distintos.

**Orden y filtros del listado.** `GET /api/pedidos` acepta `buscar`, `estado`,
`desde` y `hasta` (rango de fecha de entrega, ambos extremos inclusive y
opcionales), más `orden` y `direccion`. Ordenar por `prioridad` usa la gravedad
real —urgente, alta, media, baja— y no el orden alfabético, que dejaría `ALTA`
antes que `URGENTE`. Las columnas ordenables son una whitelist porque su nombre
se interpola en el SQL.

**Numeración.** El número de guía que ve el cliente es el propio `id_pedido`.
No existe una columna `numero_pedido` aparte: duplicaba el identificador sin
aportar reglas propias y, al calcularse con `MAX + 1`, reutilizaba números
después de un borrado — dos pedidos distintos podían terminar con la misma
guía. La identidad de PostgreSQL nunca reasigna un valor, así que el número
queda garantizado como único a lo largo de la vida del sistema. Lo asigna la
base al insertar; si el cliente envía un id, se ignora.

**Fechas.** La fecha de entrega no puede ser anterior a hoy al registrar el
pedido. Al modificarlo sólo se revalida si la fecha cambió, para no bloquear la
edición de pedidos ya vencidos. El día de referencia se calcula en la zona
horaria del taller (`ZONA_HORARIA`), no en la del contenedor.

**Importes.** Todos los montos son enteros en pesos. Se aceptan decimales sin
parte fraccionaria (`30000.0`) y se rechaza cualquier monto con centavos.

**Pagos.** Un abono no puede superar el saldo restante del pedido, y sobre un
pedido ya saldado la API responde `409`. Así el total pagado nunca queda por
encima del total.

**Asignación.** Un pedido mantiene un único responsable, pero puede cambiarse:
volver a asignar reemplaza al anterior. `DELETE /api/pedidos/<id>/asignacion`
lo deja sin responsable.

**Clientes.** Corregir el nombre o el teléfono es parte de la operación diaria,
así que el taller también puede hacerlo. Eliminar, en cambio, queda reservado a
la dueña, y sólo si el cliente no tiene pedidos: borrarlo en cascada se llevaría
sus pedidos y los pagos de esos pedidos. La API responde `409` indicando cuántos
pedidos lo están reteniendo.

**Eliminación de pedidos.** Sólo la dueña puede eliminar pedidos. El borrado es todo o
nada: si alguno de los identificadores no existe, no se borra ninguno. Las
asignaciones, pagos y detalles de insumo asociados caen por `ON DELETE
CASCADE`, y la respuesta informa cuántos pagos se eliminaron para poder
advertirlo en la interfaz.

### IVA: la tasa se guarda, el importe se calcula

Cada pedido almacena en `tasa_iva` la alícuota que regía cuando se registró.
Los importes derivados —IVA, total y saldo— **no** se guardan: los resuelve
`backend/servicios/impuestos.py` en cada consulta, usando la tasa de esa fila.

```
valor_neto = valor_base + recargo − descuento
iva        = redondear(valor_neto × pedido.tasa_iva)
total      = valor_neto + iva
saldo      = máx(total − total_pagado, 0)
```

El motivo de guardar la tasa es no reescribir el pasado. Si el IVA pasa del
19 % al 21 %, un pedido tomado con el 19 % tiene que seguir valiendo lo que
decía su boleta; si se recalculara con la tasa de hoy, el total dejaría de
cuadrar contra lo que el cliente ya pagó y el saldo cambiaría solo.

Los pedidos **nuevos** nacen con la tasa de la variable `TASA_IVA`. La copia
la hace el modelo al registrar, no el cliente de la API: mandar `tasa_iva` en
el cuerpo de la petición no tiene efecto. Así pueden convivir en la misma
tabla encargos con alícuotas distintas, y los agregados del panel suman cada
saldo con la suya.

Los importes siguen sin guardarse porque son derivados: almacenarlos abriría
la puerta a que el total y sus componentes se contradigan.

### Materiales, requerimientos y compras

`detalle_insumo` cumple tres papeles a la vez: qué necesita un pedido, si hay
que comprarlo y en qué lista salió. Al revisar el circuito aparecieron cinco
inconsistencias, todas reproducidas antes de decidir qué hacer con ellas:

1. El stock nunca se mueve: asociar un material a un pedido o marcarlo
   comprado deja `stock_actual` igual. Es una libreta que nadie actualiza.
2. *(corregido)* Se pedía comprar material que ya estaba en el estante.
   `GET /api/listas-compra/pendientes` ahora expone `cantidad_a_comprar`, que
   es lo requerido menos el stock disponible.
3. *(corregido)* Un material devuelto a pendiente quedaba trabado: seguía
   figurando como faltante, pero arrastraba la lista vieja y ninguna lista
   nueva lo tomaba. Al volver a `PENDIENTE_COMPRA` ahora se suelta de su lista.
4. *(corregido)* El total de pendientes contaba también lo ya listado, así que
   no era lo que iba a entrar en la lista siguiente.
5. Borrar un pedido vacía listas de compra ya generadas, porque sus renglones
   viven en `detalle_insumo` y caen por `ON DELETE CASCADE`.

Las tres corregidas son arreglos acotados sobre el modelo actual. La primera y
la quinta no se pueden resolver así: piden separar las tres responsabilidades
en tablas propias —un libro de movimientos de stock y un documento de compra
independiente de los pedidos—, que es un cambio de modelo.

Ese rediseño llegó a implementarse y se revirtió por riesgo de despliegue
cerca de la entrega. Queda completo en el historial, en el commit `8c573aa`,
junto con su migración y sus pruebas. `postgresql/migraciones/003` es la
vuelta atrás, para bases que alcanzaron a migrarse.

### Credenciales de acceso

`usuario` tiene `nombre_usuario` y `contrasena_hash`, ambos opcionales: no
todo trabajador entra al sistema, y exigir credenciales obligaría a inventarle
un acceso a cada uno. Un `CHECK` impide dejarlas a medias —o están las dos o
no está ninguna— y el nombre de usuario es único en toda la tabla.

La contraseña **nunca** se guarda en claro. Lo que va a la base es el resumen
con sal que produce `backend/servicios/credenciales.py` mediante Werkzeug, que
ya viene con Flask. El hash no se selecciona en ninguna consulta que alimente
una respuesta de la API.

Por ahora es sólo el modelo de datos: todavía no hay pantalla de inicio de
sesión ni rutas protegidas, y el rol se sigue eligiendo en el encabezado.

## Alcance implementado

- Registrar, buscar, modificar y eliminar clientes por nombre o teléfono.
- Registrar pedidos asociando un cliente nuevo o existente, imprimiendo la
  boleta del cliente al confirmar.
- Consultar, modificar, priorizar y actualizar el estado de pedidos.
- Ordenar el listado por guía, cliente, entrega, registro, estado o urgencia.
- Filtrar pedidos por estado y por rango de fecha de entrega.
- La urgencia tiene columna propia, con color por nivel: urgente en rojo, alta
  en naranja, media en amarillo y baja en verde.
- El número de guía es el `id_pedido` y nunca se reutiliza tras un borrado.
- Seleccionar varios pedidos y eliminarlos en una sola operación.
- Gestionar `valor_base`, descuento, recargo, pagos y saldo; el IVA y el total
  se calculan al momento.
- Asignar un pedido a un único trabajador; un trabajador puede tener varios pedidos.
- Registrar y consultar múltiples pagos o abonos.
- Crear, modificar y eliminar insumos con unidad de medida acotada; asociarlos
  a pedidos y cambiar su estado.
- Consultar pendientes y generar listas de compra con el modelo SQL existente.
- Crear y modificar trabajadores; la baja cambia su estado a `INACTIVO`.
- Cambiar entre vista de Dueña y vista de Taller sin autenticación.

No se implementan login, `Prenda`, `DetallePedido`, historial de asignaciones, movimientos históricos de stock ni `detalle_lista_compra`.

## Datos iniciales

La base incluye 3 clientes, 3 trabajadores, 5 pedidos, pagos parciales y completos, y materiales comprados y pendientes. Los datos se cargan solo cuando Docker crea el volumen por primera vez.

## Pruebas

La suite está dividida por módulo en `backend/pruebas/`: clientes, pedidos, asignaciones, pagos, insumos, listas de compra y trabajadores. Cada ejecución crea un esquema PostgreSQL temporal y lo elimina al terminar, sin tocar los datos de demostración.

El estilo del backend lo revisa [ruff](https://docs.astral.sh/ruff/), configurado en `backend/ruff.toml`:

```bash
cd backend && ruff check .
```

La configuración declara `configuracion`, `repositorios`, `rutas` y `servicios` como paquetes propios; sin eso ruff los confunde con librerías de terceros y pide mezclarlos con `flask` o `psycopg` en el mismo bloque de imports. Además de las reglas por defecto revisa el orden de los imports, sintaxis anticuada y fechas sin zona horaria —esto último importa porque los contenedores corren en UTC y Chile no—.

El frontend usa [oxlint](https://oxc.rs/docs/guide/usage/linter):

```bash
cd frontend && npm run lint
```

## Configuración

Todas se ajustan en el `.env` (ver `.env.example`):

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `TASA_IVA` | `0.19` | Alícuota que se asigna a los pedidos nuevos. |
| `ZONA_HORARIA` | `America/Santiago` | Define qué día es "hoy" al validar fechas. |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes autorizados a llamar a la API directamente. |
| `VITE_API_URL` | `/api` | Ruta que usa el frontend para llamar a la API. |
| `VITE_API_PROXY` | `http://backend:8000` | Backend al que el proxy de Vite redirige `/api`. |
| `DB_POOL_MIN` / `DB_POOL_MAX` | `1` / `10` | Tamaño del pool de conexiones a PostgreSQL. |

## Boleta del cliente

Al confirmar un pedido, el sistema manda a imprimir el comprobante que se
entrega al cliente, en media carta (5.5 x 8.5 pulgadas, la mitad de una hoja
carta). Desde el detalle de un pedido hay además un
botón para reimprimirlo.

La boleta lleva el número de guía, los datos del cliente, la fecha de registro
y de entrega, la descripción del encargo, y el **total ya con IVA, descuento y
recargo aplicados**, junto al abono y el saldo. El desglose es información
interna del taller y no aparece en el papel, igual que el estado, la prioridad,
la complejidad, las horas estimadas y la asignación.

El diseño imita el talonario de papel del taller: tinta azul, el aviso de
retiro dentro de un óvalo, los datos del cliente sobre renglones y la tabla con
recuadro.

No es un PDF generado en el servidor: la boleta se maqueta en HTML y se imprime
con el navegador (`estilos/impresion.css` oculta la interfaz y deja sólo el
comprobante). Así no hay dependencias nuevas y el mismo diálogo permite guardar
como PDF.

El margen de `@page` está en cero a propósito: es lo que hace que el navegador
deje de imprimir su propio encabezado con la URL y la fecha en el borde de la
hoja. El margen visible lo pone el `padding` de la boleta.

**Para que salga sin diálogo**, hay que abrir Chrome con `--kiosk-printing`, que
envía el trabajo directo a la impresora predeterminada. Sin ese parámetro
ningún navegador imprime en silencio: se abre la vista previa y hay que
confirmar. En Windows, se agrega al destino del acceso directo:

```
"C:\...\chrome.exe" --kiosk-printing http://localhost:5173
```

El tamaño se cambia en `@page { size }` dentro de
`frontend/src/estilos/impresion.css`: `A5 portrait` para A5, `letter` para
carta completa. Los datos del taller
—dirección, teléfono, horario de retiro— están en `frontend/src/modelos/taller.ts`.

## Cómo llega el frontend a la API

El navegador nunca llama al backend por su puerto: pide a `/api` sobre el mismo
origen desde el que cargó la página, y el servidor de Vite redirige esa ruta al
backend (`server.proxy` en `vite.config.ts`).

Esto importa apenas la aplicación se abre desde algo que no sea la propia
máquina. Con una URL absoluta tipo `http://localhost:8000/api`, ese `localhost`
lo resuelve el equipo del visitante, no el servidor, y todas las peticiones
fallan con «Failed to fetch». Yendo por el mismo origen tampoco hay CORS de por
medio ni mezcla de HTTPS con HTTP.

Para exponer la aplicación con un túnel basta con publicar el puerto 5173: la
API viaja por el mismo túnel. Los dominios permitidos se declaran en
`server.allowedHosts`.

## Nota sobre roles

El sistema no incluye autenticación. El selector “Vista operativa” adapta la interfaz y envía un encabezado de rol a la API: la vista Taller oculta y bloquea las áreas administrativas, mientras la vista Dueña permite gestionar precios, pagos, compras, insumos y trabajadores. Es un control funcional, no un mecanismo de seguridad.

Como el encabezado de rol se puede falsificar, `CORS_ORIGINS` está restringido
al frontend en lugar de aceptar cualquier origen. Sigue sin ser un mecanismo de
seguridad: es una barrera mínima mientras no exista login.
