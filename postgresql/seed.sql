-- Datos acotados para recorrer los flujos del sistema.

-- Los tres primeros tienen acceso; la contraseña de los tres es
-- 'sastrearte2026', guardada como hash scrypt con sal. Son datos de prueba:
-- en una instalación real esas claves se cambian.
-- Julián queda sin credenciales a propósito, para dejar a la vista que un
-- trabajador puede existir sin entrar al sistema.
INSERT INTO usuario (nombre, apellido, telefono, nombre_usuario, contrasena_hash, estado_usuario, tipo_usuario) VALUES
    ('Elena', 'Rojas', '+56 9 6111 2200', 'elena',
     'scrypt:32768:8:1$FFeBKdrdzswiB5DM$1d078a18b2896483772017b0e36903a1e16c5ab458d5c4fd8695d909b02852f582d6e31adc6446ffac9afaad3fd349ab77000ab9630c5e6890d51a7509344161',
     'ACTIVO', 'DUENO'),
    ('Tomás', 'Vega', '+56 9 7222 3300', 'tomas',
     'scrypt:32768:8:1$X5nALqJPNUVaRVTR$271f57169619b7b2c36dd181f701c6b1d168a043afa45ea5a554d6634c725899cc8b021099778be183c1d542e9f9d56a2ba45d458b8a9ae5a3a6def5b588898e',
     'ACTIVO', 'TRABAJADOR'),
    ('Marta', 'Silva', '+56 9 8333 4400', 'marta',
     'scrypt:32768:8:1$AvBvO8uwPJiCciCk$93b6375a349d3a42ad0c18ca835270230c0781a059cc975997bda0482228c07bf1096aaff792b57840b10ebfeacb0153eb952699255438967b8bb97f30d8c874',
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

INSERT INTO insumo (nombre, stock_actual, unidad_medida) VALUES
    ('Hilo negro', 12, 'UNIDADES'),
    ('Cierre invisible 40 cm', 4, 'UNIDADES'),
    ('Entretela termoadhesiva', 8.50, 'METROS'),
    ('Botón nácar 18 mm', 20, 'UNIDADES'),
    ('Forro satinado azul', 3.00, 'METROS');

INSERT INTO lista_compra DEFAULT VALUES;

INSERT INTO detalle_insumo (id_pedido, id_insumo, id_lista_compra, cantidad, estado_insumo) VALUES
    (1, 1, NULL, 1, 'COMPRADO'),
    (2, 3, NULL, 1.50, 'COMPRADO'),
    (2, 4, 1, 6, 'PENDIENTE_COMPRA'),
    (3, 2, 1, 1, 'PENDIENTE_COMPRA'),
    (3, 5, 1, 2.50, 'PENDIENTE_COMPRA'),
    (4, 2, NULL, 1, 'PENDIENTE_COMPRA'),
    (5, 1, NULL, 2, 'COMPRADO');
