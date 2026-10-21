import React, { useState, useEffect } from 'react';
import { getCatalogoVehiculos } from '../services/moduloCapacidadService';

export const ModuloCapacidadPage = () => {
const [catalogo, setCatalogo] = useState([]);
const [busqueda, setBusqueda] = useState('');
const [tipoFiltro, setTipoFiltro] = useState('');
const [loading, setLoading] = useState(true);

  // Estado para la vinculación Placa ↔ Modelo
const [placaInput, setPlacaInput] = useState('');
const [modeloSeleccionado, setModeloSeleccionado] = useState('');
const [vinculaciones, setVinculaciones] = useState([]);

useEffect(() => {
cargarCatalogo();
}, []);

const cargarCatalogo = async () => {
try {
    const data = await getCatalogoVehiculos();
    setCatalogo(data);
    } catch (error) {
    console.error("Error al cargar el catálogo:", error);
    } finally {
    setLoading(false);
    }
};

  // Filtrado dinámico por texto y tipo de vehículo
const vehiculosFiltrados = catalogo.filter((item) => {
const coincideTexto = 
    item.marca.toLowerCase().includes(busqueda.toLowerCase()) ||
    item.modelo.toLowerCase().includes(busqueda.toLowerCase());
    const coincideTipo = tipoFiltro === '' || item.tipo === tipoFiltro;
    return coincideTexto && coincideTipo;
});

const handleVincular = (e) => {
    e.preventDefault();
    if (!placaInput || !modeloSeleccionado) return;

    const modeloObj = catalogo.find(m => m.id === modeloSeleccionado);
    const nuevaVinculacion = {
    placa: placaInput.toUpperCase(),
    modelo: `${modeloObj.marca} ${modeloObj.modelo}`,
    volumen: modeloObj.volumen_util_m3,
    carga: modeloObj.carga_util_kg
    };

    setVinculaciones([...vinculaciones, nuevaVinculacion]);
    setPlacaInput('');
    setModeloSeleccionado('');
};

return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
    <h2>Catálogo de Vehículos y Capacidad</h2>

      {/* SECCIÓN 1: VINCULACIÓN PLACA ↔ MODELO */}
    <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
        <h3>Vinculación de Placa a Modelo del Catálogo</h3>
        <form onSubmit={handleVincular} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <input
            type="text"
            placeholder="Placa (ej. ABC-123)"
            value={placaInput}
            onChange={(e) => setPlacaInput(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            required
        />
        <select
            value={modeloSeleccionado}
            onChange={(e) => setModeloSeleccionado(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            required
        >
            <option value="">-- Seleccionar Modelo --</option>
            {catalogo.map((v) => (
            <option key={v.id} value={v.id}>
                {v.marca} {v.modelo} ({v.tipo})
            </option>
            ))}
        </select>
        <button type="submit" style={{ padding: '8px 16px', background: '#007bff', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Vincular Placa
        </button>
        </form>

        {vinculaciones.length > 0 && (
        <table style={{ width: '100%', marginTop: '15px', borderCollapse: 'collapse', background: '#fff' }}>
            <thead>
            <tr style={{ background: '#e0e0e0', textAlign: 'left' }}>
                <th style={{ padding: '8px' }}>Placa</th>
                <th style={{ padding: '8px' }}>Modelo Heredado</th>
                <th style={{ padding: '8px' }}>Volumen Útil (m³)</th>
                <th style={{ padding: '8px' }}>Carga Útil (kg)</th>
            </tr>
            </thead>
            <tbody>
            {vinculaciones.map((v, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '8px' }}><strong>{v.placa}</strong></td>
                <td style={{ padding: '8px' }}>{v.modelo}</td>
                <td style={{ padding: '8px' }}>{v.volumen} m³</td>
                <td style={{ padding: '8px' }}>{v.carga} kg</td>
                </tr>
            ))}
            </tbody>
        </table>
        )}
    </div>

      {/* SECCIÓN 2: BUSCADOR Y FILTROS DEL CATÁLOGO */}
    <h3>Catálogo Oficial ({vehiculosFiltrados.length} modelos)</h3>
    <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <input
        type="text"
        placeholder="Buscar por marca o modelo..."
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        style={{ padding: '8px', width: '250px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <select
        value={tipoFiltro}
        onChange={(e) => setTipoFiltro(e.target.value)}
        style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        >
        <option value="">Todos los tipos</option>
        <option value="pickup">Pickup</option>
        <option value="furgoneta">Furgoneta</option>
        <option value="van">Van</option>
        <option value="camion_ligero">Camión Ligero</option>
        <option value="suv">SUV</option>
        </select>
    </div>

      {/* TABLA DEL CATÁLOGO */}
    {loading ? (
        <p>Cargando catálogo...</p>
    ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
            <tr style={{ background: '#343a40', color: '#fff', textAlign: 'left' }}>
            <th style={{ padding: '10px' }}>Marca</th>
            <th style={{ padding: '10px' }}>Modelo</th>
            <th style={{ padding: '10px' }}>Tipo</th>
            <th style={{ padding: '10px' }}>Dimensiones (L x A x H)</th>
            <th style={{ padding: '10px' }}>Volumen (m³)</th>
            <th style={{ padding: '10px' }}>Carga Max (kg)</th>
            <th style={{ padding: '10px' }}>Fuente</th>
            </tr>
        </thead>
        <tbody>
            {vehiculosFiltrados.map((item) => (
            <tr key={item.id} style={{ borderBottom: '1px solid #ccc' }}>
                <td style={{ padding: '10px' }}><strong>{item.marca}</strong></td>
                <td style={{ padding: '10px' }}>{item.modelo}</td>
                <td style={{ padding: '10px' }}>{item.tipo}</td>
                <td style={{ padding: '10px' }}>{item.largo_m} x {item.ancho_m} x {item.alto_m} m</td>
                <td style={{ padding: '10px' }}>{item.volumen_util_m3} m³</td>
                <td style={{ padding: '10px' }}>{item.carga_util_kg} kg</td>
                <td style={{ padding: '10px', fontSize: '0.85em', color: '#555' }}>{item.fuente}</td>
            </tr>
            ))}
        </tbody>
        </table>
    )}
    </div>
);
};