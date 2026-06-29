// Configuración de Expo (reemplaza a app.json para poder leer variables de
// entorno). La clave de Google Maps se inyecta desde EXPO_PUBLIC_GOOGLE_MAPS_KEY:
// basta pegarla en mobile/.env y reconstruir el dev build. El mapa nativo
// (MapaNativo, Google Maps) y la ubicación en segundo plano NO funcionan en
// Expo Go: requieren un build de desarrollo (expo-dev-client).
const GOOGLE_MAPS_KEY = process.env.EXPO_PUBLIC_GOOGLE_MAPS_KEY ?? "";

export default {
  expo: {
    name: "GeoTrack Conductor",
    slug: "geotrack-conductor",
    scheme: "geotrack",
    version: "1.0.0",
    orientation: "portrait",
    userInterfaceStyle: "light",
    newArchEnabled: true,
    ios: {
      supportsTablet: true,
      // Solo se define la clave de Google si está presente (iOS usa Apple Maps por defecto).
      ...(GOOGLE_MAPS_KEY ? { config: { googleMapsApiKey: GOOGLE_MAPS_KEY } } : {}),
      infoPlist: {
        NSLocationWhenInUseUsageDescription:
          "Usamos tu ubicación para ordenar tu ruta de entregas desde donde estás.",
        NSLocationAlwaysAndWhenInUseUsageDescription:
          "Usamos tu ubicación, incluso en segundo plano, para seguir tu ruta activa en tiempo real.",
        // Permite que el rastreo de ubicación siga con la app en segundo plano (iOS).
        UIBackgroundModes: ["location"],
      },
    },
    android: {
      package: "com.siolsava.geotrack",
      // Permisos de ubicación (fina/gruesa + segundo plano) y de servicio en
      // primer plano para seguir rastreando la ruta con la app en background.
      permissions: [
        "ACCESS_FINE_LOCATION",
        "ACCESS_COARSE_LOCATION",
        "ACCESS_BACKGROUND_LOCATION",
        "FOREGROUND_SERVICE",
        "FOREGROUND_SERVICE_LOCATION",
        "CAMERA",
      ],
      config: {
        googleMaps: { apiKey: GOOGLE_MAPS_KEY },
      },
    },
    plugins: [
      "expo-router",
      "expo-secure-store",
      // expo-dev-client: necesario para el build de desarrollo (mapa nativo +
      // ubicación en segundo plano no funcionan en Expo Go).
      "expo-dev-client",
      [
        "expo-location",
        {
          // Mensajes de permiso (foreground y "siempre"/segundo plano) e indicación
          // de que la app usa ubicación en segundo plano en Android.
          locationAlwaysAndWhenInUsePermission:
            "Usamos tu ubicación, incluso en segundo plano, para seguir tu ruta activa en tiempo real.",
          locationWhenInUsePermission:
            "Usamos tu ubicación para ordenar tu ruta de entregas desde donde estás.",
          isAndroidBackgroundLocationEnabled: true,
        },
      ],
      [
        "expo-image-picker",
        {
          photosPermission: "Necesitamos tu galería para adjuntar la foto de entrega (POD).",
          cameraPermission: "Necesitamos la cámara para tomar la foto de entrega (POD).",
        },
      ],
      [
        "expo-camera",
        {
          cameraPermission: "Necesitamos la cámara para escanear los códigos QR al validar la carga.",
        },
      ],
      "expo-font",
    ],
  },
};
