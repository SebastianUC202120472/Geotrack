#!/usr/bin/env bash
# .devcontainer/setup.sh
# Se ejecuta UNA vez al crear el Codespace (postCreateCommand).
#  - Genera el .env raíz a partir de los Codespaces Secrets (o valores por defecto).
#  - Genera mobile/.env apuntando a la URL pública del backend en este Codespace.
#  - Instala las dependencias de la app móvil (Expo).
# NO contiene secretos: todo se lee de variables de entorno (Codespaces Secrets).
set -e
cd "$(dirname "$0")/.."   # raíz del repo

if [ -n "${DOTENV}" ]; then
  # OPCIÓN FÁCIL: pegaste tu .env completo en UN secreto llamado DOTENV. Se usa tal cual.
  echo ">> Usando el secret DOTENV completo como .env"
  printf '%s\n' "${DOTENV}" > .env
else
  echo ">> Generando .env raíz desde secretos individuales..."
  cat > .env <<EOF
# Generado automáticamente por el devcontainer. NO subir al repo.
POSTGRES_USER=sava_admin
POSTGRES_PASSWORD=sava_password123
POSTGRES_DB=siol_sava_db

# Base de datos: usa el Codespaces Secret DATABASE_URL (Supabase). Si no está, cae al
# Postgres local del compose (vacío, sin tus datos de demo).
DATABASE_URL=${DATABASE_URL:-postgresql://sava_admin:sava_password123@db:5432/siol_sava_db}

SECRET_KEY=${SECRET_KEY:-dev-inseguro-cambiar-en-produccion}
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=*

ADMIN_EMAIL=${ADMIN_EMAIL:-admin@siol.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

# Mapas/geocoding (opcionales). Vacíos = OpenStreetMap / Nominatim (gratis).
VITE_GOOGLE_MAPS_KEY=${VITE_GOOGLE_MAPS_KEY:-}
GOOGLE_GEOCODING_KEY=${GOOGLE_GEOCODING_KEY:-}

# Correo (opcional). Por defecto desactivado.
MAIL_ENABLED=${MAIL_ENABLED:-false}
MAIL_ADDRESS=${MAIL_ADDRESS:-}
MAIL_PASSWORD=${MAIL_PASSWORD:-}
IMAP_HOST=${IMAP_HOST:-imap.gmail.com}
IMAP_PORT=${IMAP_PORT:-993}
SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}
SMTP_PORT=${SMTP_PORT:-587}
MAIL_FOLDER=${MAIL_FOLDER:-INBOX}
MAIL_FROM_NAME=${MAIL_FROM_NAME:-SAVA S.A.C.}
EOF
fi

if [ -z "${DOTENV}" ] && [ -z "${DATABASE_URL}" ]; then
  echo "!! AVISO: no hay secret DOTENV ni DATABASE_URL. Se usará el Postgres local (vacío)."
  echo "   Para ver tus datos de Supabase, agrega el secreto DOTENV o DATABASE_URL (ver .devcontainer/README.md)."
fi

echo ">> Generando mobile/.env (URL pública del backend en Codespaces)..."
API_HOST="http://localhost:8000"
if [ -n "${CODESPACE_NAME}" ]; then
  API_HOST="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
fi
cat > mobile/.env <<EOF
# Generado automáticamente por el devcontainer.
EXPO_PUBLIC_API_URL=${API_HOST}/api
EXPO_PUBLIC_GOOGLE_MAPS_KEY=${EXPO_PUBLIC_GOOGLE_MAPS_KEY:-${VITE_GOOGLE_MAPS_KEY:-}}
EOF
echo "   EXPO_PUBLIC_API_URL=${API_HOST}/api"

echo ">> Instalando dependencias de la app móvil (Expo)..."
( cd mobile && npm install --no-audit --no-fund ) || echo "!! npm install móvil falló (puedes reintentar luego)."

echo ">> Setup completo. Al iniciar, el backend y el panel se levantan solos (postStart)."
