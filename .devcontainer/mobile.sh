#!/usr/bin/env bash
# .devcontainer/mobile.sh
# Arranca la app móvil (Expo) en modo TÚNEL para que tu teléfono (Expo Go) la
# alcance por internet, ya que el Codespace está en la nube (no en tu red WiFi).
# El backend lo consume por la URL pública del Codespace (ver mobile/.env).
set -e
cd "$(dirname "$0")/../mobile"

echo ">> IMPORTANTE: el puerto 8000 debe estar en visibilidad PUBLIC en la pestaña PORTS"
echo "   para que tu teléfono pueda llamar a la API. (Click derecho en 8000 -> Port Visibility -> Public.)"
echo ">> Iniciando Expo en modo túnel. Escanea el QR con Expo Go..."
npx expo start --tunnel -c
