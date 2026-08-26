#!/usr/bin/env bash
# Arranque de SastreArte en producción (ver render.yaml).
#
# Un único servicio sirve la API y el frontend ya compilado, así que el
# navegador siempre pide al mismo origen y no hay CORS de por medio.
#
# Sólo depende de PORT y DATABASE_URL, que es lo que inyecta cualquier
# plataforma de este tipo, así que no está atado a Render.
set -euo pipefail

cd "$(dirname "$0")"

# La plataforma inyecta PORT; en local vale el 8000 de siempre.
PUERTO="${PORT:-8000}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: falta DATABASE_URL. Conectá la base de datos al servicio." >&2
  exit 1
fi

if [[ ! -d frontend/dist ]]; then
  echo "AVISO: no existe frontend/dist; se servirá sólo la API." >&2
fi

echo "==> Preparando la base de datos"
python backend/inicializar_base.py

echo "==> SastreArte escuchando en 0.0.0.0:${PUERTO}"
exec gunicorn "app:app" \
  --chdir backend \
  --bind "0.0.0.0:${PUERTO}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
