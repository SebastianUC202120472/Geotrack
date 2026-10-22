import axios from 'axios';

// Uso de variable de entorno para flexibilidad en Docker/Producción
const API_BASE_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/modulo-capacidad`
  : 'http://localhost:8000/api/modulo-capacidad';

export const obtenerCatalogoModelos = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/catalogo`);
    return response.data;
  } catch (error) {
    console.error('Error al obtener el catálogo de modelos:', error);
    throw error;
  }
};

export const vincularPlacaModelo = async (placa, modeloId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/vincular`, {
      placa: placa.toUpperCase(),
      modelo_id: modeloId
    });
    return response.data;
  } catch (error) {
    console.error('Error al guardar la vinculación:', error);
    throw error;
  }
};

export const obtenerVinculaciones = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/vinculaciones`);
    return response.data;
  } catch (error) {
    console.error('Error al consultar historial de vinculaciones:', error);
    return [];
  }
};