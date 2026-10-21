import api from './api'; // Importa la instancia de Axios configurada en tu proyecto

export const getCatalogoVehiculos = async () => {
  const response = await api.get('/api/modulo-capacidad/catalogo');
  return response.data;
};