export const getCatalogoVehiculos = async () => {
  const response = await fetch('/api/modulo-capacidad/catalogo');
  if (!response.ok) {
    throw new Error(`Error en la petición: ${response.status}`);
  }
  return await response.json();
};