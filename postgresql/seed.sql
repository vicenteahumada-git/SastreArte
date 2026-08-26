-- Datos acotados para recorrer los flujos del sistema.

-- Usuarios de prueba con contraseñas en texto plano (demo local).
-- En producción nunca se guardan así.
INSERT INTO usuario (nombre, apellido, telefono, nombre_usuario, contrasena_hash, estado_usuario, tipo_usuario) VALUES
    ('Elena', 'Rojas', '+56 9 6111 2200', 'elena',
     'sastrearte2026',
     'ACTIVO', 'DUENO'),
    ('Tomás', 'Vega', '+56 9 7222 3300', 'tomas',
     'sastrearte2026',
     'ACTIVO', 'TRABAJADOR'),
    ('Marta', 'Silva', '+56 9 8333 4400', 'marta',
     'sastrearte2026',
     'ACTIVO', 'TRABAJADOR'),
    ('Julián', 'Pérez', '+56 9 9444 5500', NULL, NULL, 'INACTIVO', 'TRABAJADOR');

INSERT INTO cliente (nombre, telefono) VALUES
    ('Amalia Fuentes', '+56 9 5010 1020'),
    ('Diego Morales', '+56 9 6020 2030'),
    ('Sofía Contreras', '+56 9 7030 3040');

-- Las guías quedan numeradas 1..5 por la identidad de la tabla.
-- La tasa va explícita: es la que regía cuando se tomó cada encargo y queda
-- congelada ahí, así el pedido siempre vale lo que decía su boleta.
INSERT INTO pedido (
    id_cliente, fecha_entrega, descripcion, estado, prioridad,
    complejidad, tiempo_estimado, tasa_iva, valor_base, descuento, recargo
) VALUES
    (1, CURRENT_DATE + 2, 'Basta y ajuste de cintura en pantalón de vestir gris.', 'EN_PROCESO', 'ALTA', 'MEDIA', INTERVAL '3 hours', 0.19, 30000, 0, 0),
    (2, CURRENT_DATE + 5, 'Ajuste de hombros y mangas en chaqueta azul marino.', 'LISTO_PARA_ENTREGA', 'MEDIA', 'ALTA', INTERVAL '6 hours', 0.19, 45000, 0, 5000),
    (3, CURRENT_DATE + 9, 'Confección de falda midi con forro y cierre invisible.', 'PENDIENTE', 'MEDIA', 'ALTA', INTERVAL '10 hours', 0.19, 80000, 10000, 0),
    (1, CURRENT_DATE + 1, 'Cambio de cierre en vestido y refuerzo de costura lateral.', 'PENDIENTE', 'URGENTE', 'MEDIA', INTERVAL '4 hours', 0.19, 25000, 0, 0),
    (2, CURRENT_DATE + 12, 'Ajuste completo de uniforme: chaqueta y dos pantalones.', 'EN_PROCESO', 'BAJA', 'ALTA', INTERVAL '12 hours', 0.19, 60000, 5000, 10000);

INSERT INTO asignacion (id_pedido, id_trabajador) VALUES
    (1, 2),
    (2, 2),
    (5, 3);

INSERT INTO pago (id_pedido, monto, metodo_pago) VALUES
    (1, 20000, 'TRANSFERENCIA'),
    (2, 59500, 'TARJETA'),
    (3, 40000, 'EFECTIVO'),
    (5, 40000, 'TRANSFERENCIA'),
    (5, 37350, 'EFECTIVO');

INSERT INTO insumo (nombre, unidad_medida) VALUES
    ('Hilo negro', 'UNIDADES'),
    ('Cierre invisible 40 cm', 'UNIDADES'),
    ('Entretela termoadhesiva', 'METROS'),
    ('Botón nácar 18 mm', 'UNIDADES'),
    ('Forro satinado azul', 'METROS');

-- El stock existente entra como inventario inicial: no hay saldo sin asiento.
INSERT INTO movimiento_insumo (id_insumo, cantidad, motivo, observacion) VALUES
    (1, 12, 'INVENTARIO_INICIAL', 'Recuento de apertura'),
    (2, 4, 'INVENTARIO_INICIAL', 'Recuento de apertura'),
    (3, 8.50, 'INVENTARIO_INICIAL', 'Recuento de apertura'),
    (4, 20, 'INVENTARIO_INICIAL', 'Recuento de apertura'),
    (5, 3.00, 'INVENTARIO_INICIAL', 'Recuento de apertura');

-- Lo que cada pedido necesita. Nada más: si hay que comprarlo lo decide la
-- cuenta entre lo requerido y lo que hay, no una marca escrita a mano.
INSERT INTO detalle_insumo (id_pedido, id_insumo, cantidad, estado_insumo) VALUES
    (1, 1, 1, 'CONSUMIDO'),
    (2, 3, 1.50, 'CONSUMIDO'),
    (2, 4, 6, 'REQUERIDO'),
    (3, 2, 1, 'REQUERIDO'),
    (3, 5, 2.50, 'REQUERIDO'),
    (4, 2, 1, 'REQUERIDO'),
    (5, 1, 2, 'CONSUMIDO');

-- Los consumos ya hechos también dejan su movimiento, para que el stock
-- cuadre con lo que efectivamente salió del estante.
INSERT INTO movimiento_insumo (id_insumo, cantidad, motivo, id_pedido, observacion) VALUES
    (1, -1, 'CONSUMO', 1, 'Consumo del pedido #1'),
    (3, -1.50, 'CONSUMO', 2, 'Consumo del pedido #2'),
    (1, -2, 'CONSUMO', 5, 'Consumo del pedido #5');
