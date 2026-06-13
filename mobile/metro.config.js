// Configuración por defecto de Metro para Expo. Habilita, entre otros, el
// soporte de los alias de TypeScript (@/...) definidos en tsconfig.json.
const { getDefaultConfig } = require("expo/metro-config");

module.exports = getDefaultConfig(__dirname);
