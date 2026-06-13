# GeoTrack — App móvil del conductor

App móvil (Expo + React Native + TypeScript) para que los conductores vean su
ruta, la inicien desde su ubicación, marquen entregas con evidencia (foto) y
consulten su historial. Consume **exclusivamente** los endpoints del conductor
del backend de GeoTrack. No tiene registro: el conductor solo inicia sesión con
las credenciales creadas desde el panel admin.

## Requisitos
- Node 18+ y la app **Expo Go** en tu teléfono (o un emulador).
- El backend de GeoTrack corriendo y accesible desde el teléfono.

## Configurar la URL del backend
El teléfono **no** puede usar `localhost`: necesita la IP de tu PC en la red local.

1. Averigua tu IPv4 (Windows: `ipconfig` → "Dirección IPv4", p. ej. `192.168.1.100`).
2. Copia `.env.example` a `.env` y ajusta:
   ```
   EXPO_PUBLIC_API_URL=http://192.168.1.100:8000/api
   ```
3. El teléfono y la PC deben estar en la **misma red WiFi**. El backend ya expone
   el puerto 8000 y acepta CORS, así que no hay que tocar nada del backend.

## Correr en desarrollo
```bash
cd mobile
npm install
npx expo install --check   # alinea versiones nativas con el SDK de Expo
npx expo start             # escanea el QR con Expo Go
```

## Mapa (nota)
- En **iOS** usa Apple Maps (no requiere clave).
- En **Android** usa Google Maps. En Expo Go funciona para desarrollo; para una
  build de producción necesitas una API key de Google Maps en
  `app.json` → `android.config.googleMaps.apiKey` y un **dev build / EAS**.

## Compilar binario (EAS)
La app no se dockeriza: se compila a binario nativo.
```bash
npm install -g eas-cli
eas login
eas build:configure
eas build --platform android   # o ios
```
Define `EXPO_PUBLIC_API_URL` (apuntando al backend de producción) en los secretos
de EAS o en el perfil de build.

## Arquitectura
```
app/                 Pantallas (expo-router): (auth)/login, (app)/index, parada/[id], historial
src/
  api/               Cliente HTTP (axios + interceptores), endpoints tipados, token seguro
  features/          Hooks de React Query por dominio (ruta, entrega)
  services/          routeService (optimización/orden de paradas)
  components/        UI componetizada (Button, Card, MapaRuta, ParadaItem, …)
  hooks/             useUbicacionActual (expo-location)
  store/             Sesión (auth) + caché de evidencias
  theme/             Tokens de diseño (colores, espaciado, tipografía)
  types/             Tipos de dominio/API
```

## Seguridad
- Token JWT guardado cifrado con `expo-secure-store` (nunca en texto plano ni en logs).
- El cliente HTTP inyecta el token en cada request; ante un 401 cierra sesión y
  vuelve al login. Las pantallas internas están protegidas en el layout raíz.
- El backend filtra por el usuario del token: el conductor solo ve y opera lo suyo.
