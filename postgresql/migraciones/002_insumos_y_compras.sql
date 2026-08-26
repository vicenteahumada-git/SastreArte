-- Migración 002: separa requerimiento, compra y movimientos de stock.
--
-- Para bases que YA existen. Una base nueva no la necesita.
--
--   psql "<External Connection String de Render>" -f 002_insumos_y_compras.sql
--
-- Va dentro de una transacción: o se aplica entera o no se aplica nada.
-- No es idempotente como la 001, porque convierte datos: correrla dos veces
-- duplicaría los movimientos de inventario inicial. La guarda del final lo
-- impide.

BEGIN;

-- Si movimiento_insumo ya existe, la migración ya corrió.
DO $$
BEGIN
    IF to_regclass('movimiento_insumo') IS NOT NULL THEN
        RAISE EXCEPTION 'La migración 002 ya fue aplicada; no se repite.';
    END IF;
END $$;

-- 1. Libro de movimientos -----------------------------------------------
CREATE TABLE movimiento_insumo (
    id_movimiento BIGINT GENERATED ALWAYS AS IDENTITY,
    id_insumo BIGINT NOT NULL,
    cantidad NUMERIC(12,2) NOT NULL,
    motivo VARCHAR(20) NOT NULL,
    id_pedido BIGINT,
    id_lista_compra BIGINT,
    observacion VARCHAR(200),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_movimiento_insumo PRIMARY KEY (id_movimiento),
    CONSTRAINT fk_movimiento_insumo FOREIGN KEY (id_insumo) REFERENCES insumo(id_insumo),
    CONSTRAINT fk_movimiento_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE SET NULL,
    CONSTRAINT fk_movimiento_lista FOREIGN KEY (id_lista_compra) REFERENCES lista_compra(id_lista_compra) ON DELETE SET NULL,
    CONSTRAINT chk_movimiento_cantidad CHECK (cantidad <> 0),
    CONSTRAINT chk_movimiento_motivo CHECK (
        motivo IN ('INVENTARIO_INICIAL', 'COMPRA', 'CONSUMO', 'AJUSTE', 'DEVOLUCION')
    ),
    CONSTRAINT chk_movimiento_signo CHECK (
        (motivo IN ('COMPRA', 'DEVOLUCION') AND cantidad > 0)
        OR (motivo = 'CONSUMO' AND cantidad < 0)
        OR motivo IN ('INVENTARIO_INICIAL', 'AJUSTE')
    )
);

-- El stock que había en la columna pasa a ser el asiento de apertura. Así
-- ninguna existencia queda sin explicación en el libro.
INSERT INTO movimiento_insumo (id_insumo, cantidad, motivo, observacion)
SELECT id_insumo, stock_actual, 'INVENTARIO_INICIAL',
       'Saldo trasladado al migrar'
FROM insumo
WHERE stock_actual <> 0;

ALTER TABLE insumo DROP COLUMN stock_actual;

-- Una base en uso puede tener el mismo material cargado dos veces. Antes de
-- exigir unicidad se desempatan los repetidos agregando un sufijo, en vez de
-- fusionarlos: fusionar obligaría a repuntar pedidos y compras, y dos filas
-- con el mismo nombre no siempre son el mismo material. Renombrar es
-- reversible; fusionar mal, no.
WITH repetidos AS (
    SELECT id_insumo,
           ROW_NUMBER() OVER (PARTITION BY lower(nombre) ORDER BY id_insumo) AS orden
    FROM insumo
)
UPDATE insumo i
SET nombre = i.nombre || ' (' || r.orden || ')'
FROM repetidos r
WHERE r.id_insumo = i.id_insumo AND r.orden > 1;

-- Sobre lower(nombre), que es como compara el servicio.
CREATE UNIQUE INDEX uq_insumo_nombre ON insumo (lower(nombre));

CREATE VIEW vista_insumos AS
SELECT
    i.id_insumo, i.nombre, i.unidad_medida,
    COALESCE(m.stock, 0) AS stock_actual
FROM insumo i
LEFT JOIN (
    SELECT id_insumo, SUM(cantidad) AS stock
    FROM movimiento_insumo
    GROUP BY id_insumo
) m ON m.id_insumo = i.id_insumo;

-- 2. La lista de compra pasa a ser un documento con estado ---------------
ALTER TABLE lista_compra
    ADD COLUMN fecha_recepcion TIMESTAMP,
    ADD COLUMN estado VARCHAR(15) NOT NULL DEFAULT 'ABIERTA';

ALTER TABLE lista_compra
    ADD CONSTRAINT chk_estado_lista CHECK (estado IN ('ABIERTA', 'RECIBIDA', 'ANULADA')),
    ADD CONSTRAINT chk_recepcion_coherente CHECK (
        (estado = 'RECIBIDA') = (fecha_recepcion IS NOT NULL)
    );

CREATE TABLE detalle_lista_compra (
    id_lista_compra BIGINT NOT NULL,
    id_insumo BIGINT NOT NULL,
    cantidad_solicitada NUMERIC(12,2) NOT NULL,
    cantidad_recibida NUMERIC(12,2),
    CONSTRAINT pk_detalle_lista_compra PRIMARY KEY (id_lista_compra, id_insumo),
    CONSTRAINT fk_detalle_lista FOREIGN KEY (id_lista_compra) REFERENCES lista_compra(id_lista_compra) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_lista_insumo FOREIGN KEY (id_insumo) REFERENCES insumo(id_insumo),
    CONSTRAINT chk_cantidad_solicitada CHECK (cantidad_solicitada > 0),
    CONSTRAINT chk_cantidad_recibida CHECK (cantidad_recibida IS NULL OR cantidad_recibida >= 0)
);

-- Las listas viejas se reconstruyen desde detalle_insumo, que era donde
-- vivían sus renglones. A partir de acá dejan de depender de los pedidos.
INSERT INTO detalle_lista_compra (id_lista_compra, id_insumo, cantidad_solicitada)
SELECT id_lista_compra, id_insumo, SUM(cantidad)
FROM detalle_insumo
WHERE id_lista_compra IS NOT NULL
GROUP BY id_lista_compra, id_insumo;

-- 3. detalle_insumo se queda sólo con lo que el pedido necesita ----------
-- El estado se traduce: lo que estaba COMPRADO ya salió del estante, así que
-- pasa a CONSUMIDO; el resto queda REQUERIDO.
ALTER TABLE detalle_insumo DROP CONSTRAINT chk_estado_insumo;

UPDATE detalle_insumo
SET estado_insumo = CASE
    WHEN estado_insumo = 'COMPRADO' THEN 'CONSUMIDO'
    ELSE 'REQUERIDO'
END;

-- Los consumos heredados dejan su asiento, para que el stock refleje lo que
-- de verdad salió. Se registran con la fecha de hoy porque la tabla vieja no
-- guardaba cuándo ocurrieron.
INSERT INTO movimiento_insumo (id_insumo, cantidad, motivo, id_pedido, observacion)
SELECT id_insumo, -cantidad, 'CONSUMO', id_pedido,
       'Consumo trasladado al migrar'
FROM detalle_insumo
WHERE estado_insumo = 'CONSUMIDO';

ALTER TABLE detalle_insumo DROP COLUMN id_lista_compra;
ALTER TABLE detalle_insumo ALTER COLUMN estado_insumo SET DEFAULT 'REQUERIDO';
ALTER TABLE detalle_insumo
    ADD CONSTRAINT chk_estado_insumo CHECK (estado_insumo IN ('REQUERIDO', 'CONSUMIDO'));

CREATE INDEX idx_movimiento_insumo ON movimiento_insumo(id_insumo);
CREATE INDEX idx_detalle_lista_insumo ON detalle_lista_compra(id_insumo);

COMMIT;
