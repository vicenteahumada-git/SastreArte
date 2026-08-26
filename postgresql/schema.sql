-- SASTREARTE - Esquema de base de datos - PostgreSQL 16

CREATE TABLE usuario (
    id_usuario BIGINT GENERATED ALWAYS AS IDENTITY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    telefono VARCHAR(30),
    -- Credenciales de acceso. Son opcionales: no todo trabajador entra al
    -- sistema, y exigirlas obligaría a inventar un usuario para cada uno.
    nombre_usuario VARCHAR(50),
    -- Nunca la contraseña en claro: acá va el resumen (hash) con su sal,
    -- que es lo que produce servicios/credenciales.py.
    contrasena_hash VARCHAR(255),
    estado_usuario VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    tipo_usuario VARCHAR(15) NOT NULL,
    CONSTRAINT pk_usuario PRIMARY KEY (id_usuario),
    CONSTRAINT uq_usuario_nombre_usuario UNIQUE (nombre_usuario),
    -- O están las dos o no está ninguna: un usuario sin clave no podría
    -- entrar, y una clave sin usuario no la reclama nadie.
    CONSTRAINT chk_credenciales_completas CHECK (
        (nombre_usuario IS NULL) = (contrasena_hash IS NULL)
    ),
    CONSTRAINT chk_nombre_usuario CHECK (
        nombre_usuario IS NULL OR nombre_usuario ~ '^[a-z0-9._-]{3,50}$'
    ),
    CONSTRAINT chk_estado_usuario CHECK (estado_usuario IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT chk_tipo_usuario CHECK (tipo_usuario IN ('DUENO', 'TRABAJADOR'))
);

CREATE TABLE cliente (
    id_cliente BIGINT GENERATED ALWAYS AS IDENTITY,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    CONSTRAINT pk_cliente PRIMARY KEY (id_cliente)
);

CREATE TABLE pedido (
    -- id_pedido es también el número de guía que ve el cliente: la identidad
    -- de PostgreSQL nunca reutiliza valores, ni siquiera tras un borrado.
    id_pedido BIGINT GENERATED ALWAYS AS IDENTITY,
    id_cliente BIGINT NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega DATE NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(50) NOT NULL,
    prioridad VARCHAR(50),
    complejidad VARCHAR(50),
    tiempo_estimado INTERVAL,
    -- La tasa que regía cuando se registró el pedido. Se guarda para que un
    -- cambio de alícuota no reescriba el pasado: los pedidos viejos siguen
    -- valiendo lo que decía su boleta. La tasa para los pedidos nuevos sale
    -- de la variable TASA_IVA (servicios/impuestos.py); el DEFAULT es sólo
    -- una red para inserciones hechas por fuera de la aplicación.
    tasa_iva NUMERIC(5,4) NOT NULL DEFAULT 0.19,
    valor_base BIGINT NOT NULL,
    descuento BIGINT NOT NULL DEFAULT 0,
    recargo BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT pk_pedido PRIMARY KEY (id_pedido),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente),
    CONSTRAINT chk_tasa_iva CHECK (tasa_iva >= 0 AND tasa_iva <= 1),
    CONSTRAINT chk_valor_base CHECK (valor_base >= 0),
    CONSTRAINT chk_descuento CHECK (descuento >= 0),
    CONSTRAINT chk_recargo CHECK (recargo >= 0),
    CONSTRAINT chk_valor_neto_no_negativo CHECK ((valor_base + recargo - descuento) >= 0),
    CONSTRAINT chk_tiempo_estimado CHECK (tiempo_estimado IS NULL OR tiempo_estimado >= INTERVAL '0'),
    CONSTRAINT chk_estado_pedido CHECK (
        estado IN ('PENDIENTE', 'EN_PROCESO', 'LISTO_PARA_ENTREGA', 'ENTREGADO', 'CANCELADO')
    ),
    CONSTRAINT chk_prioridad CHECK (
        prioridad IS NULL OR prioridad IN ('BAJA', 'MEDIA', 'ALTA', 'URGENTE')
    ),
    CONSTRAINT chk_complejidad CHECK (
        complejidad IS NULL OR complejidad IN ('BAJA', 'MEDIA', 'ALTA')
    )
);

CREATE TABLE asignacion (
    id_pedido BIGINT NOT NULL,
    id_trabajador BIGINT NOT NULL,
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_asignacion PRIMARY KEY (id_pedido),
    CONSTRAINT fk_asignacion_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_asignacion_trabajador FOREIGN KEY (id_trabajador) REFERENCES usuario(id_usuario)
);

CREATE TABLE pago (
    id_pago BIGINT GENERATED ALWAYS AS IDENTITY,
    id_pedido BIGINT NOT NULL,
    monto BIGINT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(20) NOT NULL,
    CONSTRAINT pk_pago PRIMARY KEY (id_pago),
    CONSTRAINT fk_pago_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    CONSTRAINT chk_pago_monto CHECK (monto > 0),
    CONSTRAINT chk_metodo_pago CHECK (metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA', 'TARJETA'))
);

CREATE TABLE insumo (
    id_insumo BIGINT GENERATED ALWAYS AS IDENTITY,
    nombre VARCHAR(150) NOT NULL,
    stock_actual NUMERIC(12,2) NOT NULL DEFAULT 0,
    unidad_medida VARCHAR(30) NOT NULL,
    CONSTRAINT pk_insumo PRIMARY KEY (id_insumo),
    CONSTRAINT chk_stock_actual CHECK (stock_actual >= 0),
    CONSTRAINT chk_unidad_medida CHECK (
        unidad_medida IN ('MM', 'CM', 'METROS', 'UNIDADES')
    )
);

CREATE TABLE lista_compra (
    id_lista_compra BIGINT GENERATED ALWAYS AS IDENTITY,
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lista_compra PRIMARY KEY (id_lista_compra)
);

CREATE TABLE detalle_insumo (
    id_pedido BIGINT NOT NULL,
    id_insumo BIGINT NOT NULL,
    id_lista_compra BIGINT,
    cantidad NUMERIC(12,2) NOT NULL,
    estado_insumo VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE_COMPRA',
    CONSTRAINT pk_detalle_insumo PRIMARY KEY (id_pedido, id_insumo),
    CONSTRAINT fk_detalle_insumo_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_insumo_insumo FOREIGN KEY (id_insumo) REFERENCES insumo(id_insumo),
    CONSTRAINT fk_detalle_insumo_lista FOREIGN KEY (id_lista_compra) REFERENCES lista_compra(id_lista_compra) ON DELETE SET NULL,
    CONSTRAINT chk_cantidad_insumo CHECK (cantidad > 0),
    CONSTRAINT chk_estado_insumo CHECK (estado_insumo IN ('PENDIENTE_COMPRA', 'COMPRADO'))
);

-- La vista sólo resuelve lo que depende de los datos almacenados:
-- el valor neto del pedido y cuánto se le pagó. El IVA, el total y el saldo
-- restante los calcula la capa de servicios con la tasa de cada pedido
-- (que viaja en p.*), porque son regla de negocio y no persistencia.
CREATE VIEW vista_pedidos AS
SELECT
    p.*,
    (p.valor_base + p.recargo - p.descuento) AS valor_neto,
    COALESCE(pp.total_pagado, 0) AS total_pagado
FROM pedido p
LEFT JOIN (
    SELECT id_pedido, SUM(monto) AS total_pagado
    FROM pago
    GROUP BY id_pedido
) pp ON pp.id_pedido = p.id_pedido;

CREATE INDEX idx_cliente_nombre ON cliente(nombre);
CREATE INDEX idx_cliente_telefono ON cliente(telefono);
CREATE INDEX idx_pedido_cliente ON pedido(id_cliente);
CREATE INDEX idx_pedido_estado ON pedido(estado);
CREATE INDEX idx_pedido_fecha_entrega ON pedido(fecha_entrega);
CREATE INDEX idx_asignacion_trabajador ON asignacion(id_trabajador);
CREATE INDEX idx_pago_pedido ON pago(id_pedido);
CREATE INDEX idx_detalle_insumo_insumo ON detalle_insumo(id_insumo);

