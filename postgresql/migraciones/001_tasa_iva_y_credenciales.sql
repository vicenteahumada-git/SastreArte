-- Migración 001: tasa de IVA por pedido y credenciales de usuario.
--
-- Para bases que YA existen y fueron creadas con el esquema anterior.
-- Una base nueva no la necesita: schema.sql ya trae todo esto.
--
--   psql "<External Connection String de Render>" -f 001_tasa_iva_y_credenciales.sql
--
-- Es idempotente: se puede correr dos veces sin romper nada. Y va dentro de
-- una transacción, así que o se aplica entera o no se aplica nada.
--
-- Queda una diferencia cosmética contra una base creada de cero: ADD COLUMN
-- agrega al final, así que tasa_iva y las credenciales quedan en otra
-- posición. Las columnas, tipos, valores por defecto y restricciones son
-- idénticos, y ninguna consulta del proyecto depende del orden —todas nombran
-- las columnas—, así que no tiene efecto práctico.

BEGIN;

-- 1. La tasa que regía cuando se registró el pedido ---------------------
-- Los pedidos que ya existen se quedan con 0.19, que es la tasa con la que
-- fueron cobrados; por eso el DEFAULT sirve también como relleno histórico.
ALTER TABLE pedido
    ADD COLUMN IF NOT EXISTS tasa_iva NUMERIC(5,4) NOT NULL DEFAULT 0.19;

ALTER TABLE pedido DROP CONSTRAINT IF EXISTS chk_tasa_iva;
ALTER TABLE pedido
    ADD CONSTRAINT chk_tasa_iva CHECK (tasa_iva >= 0 AND tasa_iva <= 1);

-- 2. Credenciales de acceso ---------------------------------------------
ALTER TABLE usuario
    ADD COLUMN IF NOT EXISTS nombre_usuario VARCHAR(50),
    ADD COLUMN IF NOT EXISTS contrasena_hash VARCHAR(255);

ALTER TABLE usuario DROP CONSTRAINT IF EXISTS uq_usuario_nombre_usuario;
ALTER TABLE usuario
    ADD CONSTRAINT uq_usuario_nombre_usuario UNIQUE (nombre_usuario);

ALTER TABLE usuario DROP CONSTRAINT IF EXISTS chk_credenciales_completas;
ALTER TABLE usuario
    ADD CONSTRAINT chk_credenciales_completas CHECK (
        (nombre_usuario IS NULL) = (contrasena_hash IS NULL)
    );

ALTER TABLE usuario DROP CONSTRAINT IF EXISTS chk_nombre_usuario;
ALTER TABLE usuario
    ADD CONSTRAINT chk_nombre_usuario CHECK (
        nombre_usuario IS NULL OR nombre_usuario ~ '^[a-z0-9._-]{3,50}$'
    );

-- 3. Rehacer la vista ----------------------------------------------------
-- Imprescindible: PostgreSQL expande el `p.*` al crear la vista y congela
-- ahí la lista de columnas. Sin rehacerla, vista_pedidos seguiría sin
-- conocer tasa_iva por más que la columna exista en la tabla, y la API
-- fallaría con "column vp.tasa_iva does not exist".
--
-- Va DROP y no CREATE OR REPLACE porque la columna nueva se intercala antes
-- de valor_base, y REPLACE sólo admite agregar columnas al final.
DROP VIEW IF EXISTS vista_pedidos;

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

COMMIT;
