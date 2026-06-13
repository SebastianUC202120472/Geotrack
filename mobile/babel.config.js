// Configuración de Babel para Expo (incluye el soporte de expo-router).
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
  };
};
