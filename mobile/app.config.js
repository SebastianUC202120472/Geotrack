// Configuración de Expo (reemplaza a app.json para poder leer variables de
// entorno). La clave de Google Maps se inyecta desde EXPO_PUBLIC_GOOGLE_MAPS_KEY:
// basta pegarla en mobile/.env y reconstruir. Sin clave, en Expo Go el mapa usa
// la clave de Expo; la clave propia es para builds nativos (eas build).
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
      },
    },
    android: {
      package: "com.siolsava.geotrack",
      permissions: ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "CAMERA"],
      config: {
        googleMaps: { apiKey: GOOGLE_MAPS_KEY },
      },
    },
    plugins: [
      "expo-router",
      "expo-secure-store",
      [
        "expo-location",
        {
          locationWhenInUsePermission:
            "Usamos tu ubicación para ordenar tu ruta de entregas desde donde estás.",
        },
      ],
      [
        "expo-image-picker",
        {
          photosPermission: "Necesitamos tu galería para adjuntar la foto de entrega (POD).",
          cameraPermission: "Necesitamos la cámara para tomar la foto de entrega (POD).",
        },
      ],
      "expo-font",
    ],
  },
};
