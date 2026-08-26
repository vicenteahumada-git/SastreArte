-- Migración 003: vuelve atrás el rediseño de insumos de la 002.
--
-- Se aplica cuando el código se revirtió al modelo anterior y la base ya
-- había sido migrada. Sin esto, la aplicación pide columnas que la 002
-- eliminó y responde 500 en Insumos, Compras y Resumen.
--
--   psql "<External Connection String de Render>" -f 003_revertir_insumos.sql
--
-- Ejecutar el archivo COMPLETO (en DBeaver: Alt+X, no Ctrl+Enter).
-- Va dentro de una transacción: o se aplica entera o no se aplica nada.
-- Es defensiva: cada paso comprueba si hace falta, así que sirve igual si la
-- 002 había quedado a medias.

BEGIN;

-- 1. Devolver el stock a su columna --------------------------------------
-- El saldo se recalcula desde el libro de movimientos ANTES de borrarlo.
-- Se hace en dos pasos —agregar la columna, llenarla, y recién después
-- exigir que no sea negativa— porque un saldo negativo por un ajuste mal
-- cargado haría fallar el CHECK y abortaría toda la vuelta atrás.
ALTER TABLE insumo ADD COLUMN IF NOT EXISTS stock_actual NUMERIC(12,2) NOT NULL DEFAULT 0;

-- Se descartan los consumos que inventó la propia 002 al migrar. Aquellos no
-- fueron salidas reales de bodega: la 002 los dedujo de los materiales que
-- ya figuraban como comprados, y en el modelo viejo "comprado" quería decir
-- que se compró para ese pedido, no que se sacó del estante. Contarlos haría
-- que el stock volviera más bajo de lo que estaba antes de migrar.
-- Los movimientos posteriores sí se conservan: esos ocurrieron de verdad.
DO $$
BEGIN
    IF to_regclass('movimiento_insumo') IS NOT NULL THEN
        UPDATE insumo i
        SET stock_actual = GREATEST(COALESCE((
            SELECT SUM(m.cantidad) FROM movimiento_insumo m
            WHERE m.id_insumo = i.id_insumo
              AND COALESCE(m.observacion, '') <> 'Consumo trasladado al migrar'
        ), 0), 0);
    END IF;
END $$;

ALTER TABLE insumo DROP CONSTRAINT IF EXISTS chk_stock_actual;
ALTER TABLE insumo ADD CONSTRAINT chk_stock_actual CHECK (stock_actual >= 0);

-- 2. detalle_insumo vuelve a cargar con la compra ------------------------
ALTER TABLE detalle_insumo ADD COLUMN IF NOT EXISTS id_lista_compra BIGINT;

ALTER TABLE detalle_insumo DROP CONSTRAINT IF EXISTS fk_detalle_insumo_lista;
ALTER TABLE detalle_insumo
    ADD CONSTRAINT fk_detalle_insumo_lista
    FOREIGN KEY (id_lista_compra) REFERENCES lista_compra(id_lista_compra) ON DELETE SET NULL;

-- Los estados se traducen de vuelta.
ALTER TABLE detalle_insumo DROP CONSTRAINT IF EXISTS chk_estado_insumo;

UPDATE detalle_insumo
SET estado_insumo = CASE
    WHEN estado_insumo = 'CONSUMIDO' THEN 'COMPRADO'
    WHEN estado_insumo = 'REQUERIDO' THEN 'PENDIENTE_COMPRA'
    ELSE estado_insumo
END;

ALTER TABLE detalle_insumo ALTER COLUMN estado_insumo SET DEFAULT 'PENDIENTE_COMPRA';
ALTER TABLE detalle_insumo
    ADD CONSTRAINT chk_estado_insumo CHECK (estado_insumo IN ('PENDIENTE_COMPRA', 'COMPRADO'));

-- Reponer a qué lista pertenece cada material pendiente. Esto es lo único
-- que la vuelta atrás no puede reconstruir con exactitud: al generar la
-- lista, la 002 sumó las cantidades por material y perdió de qué pedido
-- venía cada una. Se reasigna la lista más reciente que pidió ese material,
-- que es lo más cercano a la realidad; si un material estaba en dos listas
-- abiertas, la más vieja queda sin sus renglones.
DO $$
BEGIN
    IF to_regclass('detalle_lista_compra') IS NOT NULL THEN
        UPDATE detalle_insumo di
        SET id_lista_compra = (
            SELECT MAX(dlc.id_lista_compra)
            FROM detalle_lista_compra dlc
            WHERE dlc.id_insumo = di.id_insumo
        )
        WHERE di.estado_insumo = 'PENDIENTE_COMPRA';
    END IF;
END $$;

-- 3. Sacar lo que agregó el rediseño -------------------------------------
DROP VIEW IF EXISTS vista_insumos;
DROP INDEX IF EXISTS uq_insumo_nombre;
DROP INDEX IF EXISTS idx_movimiento_insumo;
DROP INDEX IF EXISTS idx_detalle_lista_insumo;
DROP TABLE IF EXISTS detalle_lista_compra;
DROP TABLE IF EXISTS movimiento_insumo;

ALTER TABLE lista_compra DROP CONSTRAINT IF EXISTS chk_recepcion_coherente;
ALTER TABLE lista_compra DROP CONSTRAINT IF EXISTS chk_estado_lista;
ALTER TABLE lista_compra DROP COLUMN IF EXISTS estado;
ALTER TABLE lista_compra DROP COLUMN IF EXISTS fecha_recepcion;

COMMIT;
