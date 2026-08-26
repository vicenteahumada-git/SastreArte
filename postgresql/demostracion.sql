-- Datos para una presentación de SastreArte.
--
-- Deja la base con un taller creíble y acotado: 6 clientes, 8 pedidos en
-- distintos estados y urgencias, pagos parciales y completos, 6 materiales
-- y una lista de compra ya generada. Suficiente para recorrer todas las
-- pantallas sin que ninguna quede vacía ni tan llena que no se lea.
--
--   psql "<External Connection String de Render>" -f demostracion.sql
--
-- En DBeaver: ejecutar el archivo COMPLETO con Alt+X, no Ctrl+Enter.
--
-- OJO: borra los clientes, pedidos, pagos, insumos y compras que haya.
-- Las cuentas se recrean, incluida `owner` con su clave de siempre.
-- Va en una transacción: o entra todo o no entra nada.

BEGIN;

-- Se vacía todo y se reinician los contadores, para que las guías arranquen
-- en 1 y los números que se ven en pantalla sean los de esta demostración.
TRUNCATE TABLE detalle_insumo, pago, asignacion, pedido,
               cliente, usuario, insumo, lista_compra
    RESTART IDENTITY CASCADE;

-- --- Cuentas ---------------------------------------------------------------
-- Las contraseñas van resumidas con scrypt, que es lo que verifica el login.
--   owner    / 12345            (dueña, la cuenta que ya usabas)
--   veronica / sastrearte2026   (dueña)
--   tomas    / sastrearte2026   (trabajador)
--   marta    / sastrearte2026   (trabajadora)
-- Julián queda sin acceso a propósito: un trabajador puede existir sin
-- entrar al sistema, y sirve para mostrarlo.
INSERT INTO usuario (nombre, apellido, telefono, nombre_usuario, contrasena_hash, estado_usuario, tipo_usuario) VALUES
    ('Verónica', 'Rojas', '+56 9 8202 8816', 'veronica',
     'scrypt:32768:8:1$6Vm2ZBTvPT4s7jnY$16e33c8d1a8b4af0d9be73eafc832181f6ad6d9b547bd908339988ea33f2756a8d8edcf55869dc8045990847cf3aa9a7f2733f25431908953a2562176058c79d',
     'ACTIVO', 'DUENO'),
    ('Administrador', NULL, NULL, 'owner',
     'scrypt:32768:8:1$v0fb3UrfZtmlYzTG$3f404b9d281dec3e8c53e3abea2329c186278ed40f3709a741271a38a7035d6e94387780c9e8b4b2ee19f68347eaa5e16bf4fb5092464136af03060ad5675c4e',
     'ACTIVO', 'DUENO'),
    ('Tomás', 'Vega', '+56 9 7222 3300', 'tomas',
     'scrypt:32768:8:1$Y898jX5C0SG8O9Tq$e84104e0ddd6cf93e1ca48b0b06c0da2e8583f8b188e53048b8eed7813f3fa16fabce9eb70b605de60a7a65403092ae447134bf41e01ac0dd3b3fe2e33d16eed',
     'ACTIVO', 'TRABAJADOR'),
    ('Marta', 'Silva', '+56 9 8333 4400', 'marta',
     'scrypt:32768:8:1$sjwhh4PtE9uZ99YL$f879dbf5a85483f37c128aa821c960d7f1cb931064536b90499fa47a4d73204b12e4689a650cc73398ff5b7f1f8f61d2ec207e9495dbd3836201567dd85a861f',
     'ACTIVO', 'TRABAJADOR'),
    ('Julián', 'Pérez', '+56 9 9444 5500', NULL, NULL, 'INACTIVO', 'TRABAJADOR');

-- --- Clientes --------------------------------------------------------------
INSERT INTO cliente (nombre, telefono) VALUES
    ('Amalia Fuentes',   '+56 9 5010 1020'),
    ('Diego Morales',    '+56 9 6020 2030'),
    ('Sofía Contreras',  '+56 9 7030 3040'),
    ('Ignacio Bravo',    '+56 9 8040 4050'),
    ('Camila Undurraga', '+56 9 9050 5060'),
    ('Rodrigo Tapia',    '+56 9 4060 6070');

-- --- Pedidos ---------------------------------------------------------------
-- Las fechas son relativas a hoy para que el panel se vea vivo: hay entregas
-- vencidas, de esta semana y más adelante. Los cuatro niveles de urgencia
-- están representados, así que la tabla muestra los cuatro colores.
INSERT INTO pedido (
    id_cliente, fecha_registro, fecha_entrega, descripcion, estado, prioridad,
    complejidad, tiempo_estimado, tasa_iva, valor_base, descuento, recargo
) VALUES
    -- 1. Vencido y urgente: el caso que la dueña quiere ver primero.
    (1, CURRENT_TIMESTAMP - INTERVAL '9 days', CURRENT_DATE - 1,
     'Vestido de gala azul: entallar cintura, subir ruedo 4 cm y cambiar cierre.',
     'EN_PROCESO', 'URGENTE', 'ALTA', INTERVAL '6 hours', 0.19, 48000, 0, 0),

    -- 2. Entrega hoy.
    (2, CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_DATE,
     'Traje de novio gris: ajuste de hombros, mangas y pantalón completo.',
     'LISTO_PARA_ENTREGA', 'ALTA', 'ALTA', INTERVAL '10 hours', 0.19, 95000, 5000, 0),

    -- 3. Esta semana.
    (3, CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_DATE + 2,
     'Falda midi con forro y cierre invisible, confección a medida.',
     'EN_PROCESO', 'MEDIA', 'ALTA', INTERVAL '9 hours', 0.19, 72000, 0, 0),

    -- 4. Esta semana, recién tomado.
    (4, CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_DATE + 4,
     'Basta y ajuste de cintura en dos pantalones de vestir.',
     'PENDIENTE', 'ALTA', 'BAJA', INTERVAL '3 hours', 0.19, 26000, 0, 0),

    -- 5. Más adelante, con recargo por trabajo extra.
    (5, CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_DATE + 9,
     'Abrigo de paño: cambio de forro completo y refuerzo de botones.',
     'PENDIENTE', 'MEDIA', 'ALTA', INTERVAL '12 hours', 0.19, 88000, 0, 12000),

    -- 6. Sin apuro.
    (6, CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_DATE + 14,
     'Camisas de vestir: entallar tres, blanca, celeste y a rayas.',
     'PENDIENTE', 'BAJA', 'MEDIA', INTERVAL '5 hours', 0.19, 39000, 0, 0),

    -- 7. Entregado y pagado: alimenta el historial y la boleta saldada.
    (1, CURRENT_TIMESTAMP - INTERVAL '20 days', CURRENT_DATE - 8,
     'Chaqueta de tweed: entallar costados y acortar mangas 3 cm.',
     'ENTREGADO', 'MEDIA', 'MEDIA', INTERVAL '4 hours', 0.19, 45000, 0, 0),

    -- 8. Cancelado: muestra que el estado existe y no aparece en pendientes.
    (3, CURRENT_TIMESTAMP - INTERVAL '15 days', CURRENT_DATE - 5,
     'Blusa de seda: la clienta desistió antes de empezar.',
     'CANCELADO', 'BAJA', 'BAJA', INTERVAL '2 hours', 0.19, 30000, 0, 0);

-- --- Asignaciones ----------------------------------------------------------
-- Tomás con dos encargos y Marta con dos: se ve que un trabajador puede
-- tener varios. Quedan pedidos sin asignar a propósito, para poder asignar
-- uno en vivo durante la demostración.
INSERT INTO asignacion (id_pedido, id_trabajador) VALUES
    (1, 3),
    (2, 3),
    (3, 4),
    (7, 4);

-- --- Pagos -----------------------------------------------------------------
-- Totales con IVA al 19 %:
--   #1  48000        -> 57120   abonado 20000  -> saldo 37120
--   #2  95000-5000   -> 107100  abonado 50000  -> saldo 57100
--   #3  72000        -> 85680   abonado 85680  -> saldado
--   #5  88000+12000  -> 119000  abonado 30000  -> saldo 89000
--   #7  45000        -> 53550   abonado 53550  -> saldado
INSERT INTO pago (id_pedido, monto, fecha, metodo_pago) VALUES
    (1, 20000, CURRENT_TIMESTAMP - INTERVAL '9 days', 'EFECTIVO'),
    (2, 50000, CURRENT_TIMESTAMP - INTERVAL '6 days', 'TRANSFERENCIA'),
    (3, 40000, CURRENT_TIMESTAMP - INTERVAL '4 days', 'TARJETA'),
    (3, 45680, CURRENT_TIMESTAMP - INTERVAL '1 day',  'EFECTIVO'),
    (5, 30000, CURRENT_TIMESTAMP - INTERVAL '2 days', 'TRANSFERENCIA'),
    (7, 53550, CURRENT_TIMESTAMP - INTERVAL '20 days', 'EFECTIVO');

-- --- Materiales ------------------------------------------------------------
-- Con stock variado a propósito: algunos sobran y otros no alcanzan, que es
-- lo que hace visible el aviso de la pantalla de insumos por pedido.
INSERT INTO insumo (nombre, stock_actual, unidad_medida) VALUES
    ('Hilo negro',              24, 'UNIDADES'),
    ('Cierre invisible 40 cm',   2, 'UNIDADES'),
    ('Entretela termoadhesiva', 6.50, 'METROS'),
    ('Botón nácar 18 mm',       30, 'UNIDADES'),
    ('Forro satinado azul',     1.50, 'METROS'),
    ('Cinta métrica de repuesto', 4, 'UNIDADES');

-- --- Materiales por pedido -------------------------------------------------
-- El pedido 1 necesita 3 cierres y sólo hay 2: la fila marca "no alcanza".
-- El pedido 5 pide 4 metros de forro y hay 1.50: también falta.
INSERT INTO detalle_insumo (id_pedido, id_insumo, id_lista_compra, cantidad, estado_insumo) VALUES
    (1, 2, NULL, 3,    'PENDIENTE_COMPRA'),
    (1, 1, NULL, 2,    'COMPRADO'),
    (2, 4, NULL, 8,    'COMPRADO'),
    (3, 3, NULL, 2.00, 'COMPRADO'),
    (5, 5, NULL, 4.00, 'PENDIENTE_COMPRA'),
    (5, 3, NULL, 3.00, 'PENDIENTE_COMPRA'),
    (6, 1, NULL, 3,    'PENDIENTE_COMPRA');

-- --- Una lista de compra ya generada ---------------------------------------
-- Deja el archivador con historia. Se lleva el forro del pedido 5, así que
-- ese material aparece como "ya listado" y el resto sigue disponible para
-- generar una lista nueva en vivo.
INSERT INTO lista_compra (fecha_generacion)
VALUES (CURRENT_TIMESTAMP - INTERVAL '2 days');

UPDATE detalle_insumo SET id_lista_compra = 1
WHERE id_pedido = 5 AND id_insumo = 5;

COMMIT;

-- Comprobación rápida: 6 clientes, 8 pedidos, 6 pagos, 6 materiales.
SELECT
    (SELECT COUNT(*) FROM cliente)  AS clientes,
    (SELECT COUNT(*) FROM pedido)   AS pedidos,
    (SELECT COUNT(*) FROM pago)     AS pagos,
    (SELECT COUNT(*) FROM insumo)   AS materiales,
    (SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'TRABAJADOR') AS trabajadores;
