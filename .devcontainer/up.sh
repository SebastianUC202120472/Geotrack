#!/usr/bin/env bash
# .devcontainer/up.sh
# Se ejecuta cada vez que arranca el Codespace (postStartCommand).
# Levanta backend + frontend con Docker. La primera vez compila las imágenes
# (unos minutos); las siguientes usa la caché y es rápido.
set -e
cd "$(dirname "$0")/.."

echo ">> Levantando backend + frontend (docker compose)..."
docker compose up -d --build backend frontend

echo ""
echo "==================================================================="
echo " GeoTrack listo:"
echo "   • Panel web (admin/almacén) -> puerto 8080  (pestaña PORTS)"
echo "   • API / Swagger             -> puerto 8000  (.../docs)"
echo "   • Admin inicial: admin@siol.com / admin123"
echo ""
echo " App móvil (cuando quieras):  bash .devcontainer/mobile.sh"
echo "==================================================================="
