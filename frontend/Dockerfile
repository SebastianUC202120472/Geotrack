# =============================================================================
# Dockerfile del FRONTEND (React 19 + Vite + Tailwind)
# Build multi-etapa:  node:22-alpine  ->  nginx:1.27-alpine
# =============================================================================

# ---------- Etapa 1: build ----------
FROM node:22-alpine AS build
WORKDIR /app

# IMPORTANTE: Vite "hornea" las variables VITE_* en tiempo de COMPILACIÓN.
# Por eso las recibimos como ARG y las pasamos a ENV ANTES de `npm run build`.
# Desde docker-compose se inyectan como rutas RELATIVAS (VITE_API_URL=/api,
# VITE_WS_URL=/) para que el navegador hable siempre con Nginx (que hace de
# reverse proxy) y nunca se hardcodee localhost en el bundle.
ARG VITE_API_URL=/api
ARG VITE_WS_URL=/
ARG VITE_GOOGLE_MAPS_KEY=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_GOOGLE_MAPS_KEY=$VITE_GOOGLE_MAPS_KEY

# Instalamos dependencias de forma reproducible (usa package-lock.json).
COPY package.json package-lock.json ./
RUN npm ci

# Copiamos el resto del código y construimos el bundle de producción (-> /app/dist).
COPY . .
RUN npm run build

# ---------- Etapa 2: runtime (Nginx) ----------
FROM nginx:1.27-alpine

# Configuración de Nginx: SPA + reverse proxy hacia el servicio "backend".
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiamos SOLO el resultado del build estático.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
