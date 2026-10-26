import React, { useState } from 'react';

const CAPACIDAD_VEHICULO = {
  id: "VEH-001",
  modelo: "Furgoneta Sprinter",
  maxM3: 10.5,
  maxKg: 1200
};

export default function CalculadoraCapacidad() {
  const [cantidades, setCantidades] = useState({ S: 0, M: 0, L: 0 });
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);

  const handleChange = (tamanio, val) => {
    setCantidades(prev => ({
      ...prev,
      [tamanio]: Math.max(0, parseInt(val) || 0)
    }));
  };

  const calcularCarga = async () => {
    setCargando(true);
    const paquetes = Object.entries(cantidades)
      .filter(([_, cant]) => cant > 0)
      .map(([tamanio, cantidad]) => ({ tamanio, cantidad }));

    try {
      const res = await fetch('http://localhost:8000/api/modulo-capacidad/calcular-capacidad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vehiculo_id: CAPACIDAD_VEHICULO.id,
          capacidad_max_m3: CAPACIDAD_VEHICULO.maxM3,
          capacidad_max_kg: CAPACIDAD_VEHICULO.maxKg,
          paquetes
        })
      });
      const data = await res.json();
      setResultado(data);
    } catch (err) {
      console.error("Error al calcular:", err);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', fontFamily: 'sans-serif' }}>
      <h2> Calculadora de Capacidad y Alertas (Semana 10)</h2>
      
      <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
        <strong>Vehículo:</strong> {CAPACIDAD_VEHICULO.modelo}<br />
        <small>Límite: {CAPACIDAD_VEHICULO.maxM3} m³ / {CAPACIDAD_VEHICULO.maxKg} kg</small>
      </div>

      <h3>Tamaños Estándar</h3>
      <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
        <div>
          <label><strong>Pequeño (S):</strong></label><br />
          <small>0.05 m³ | 5 kg</small><br />
          <input 
            type="number" 
            min="0" 
            value={cantidades.S} 
            onChange={(e) => handleChange('S', e.target.value)}
            style={{ width: '80px', marginTop: '5px' }}
          />
        </div>

        <div>
          <label><strong>Mediano (M):</strong></label><br />
          <small>0.25 m³ | 20 kg</small><br />
          <input 
            type="number" 
            min="0" 
            value={cantidades.M} 
            onChange={(e) => handleChange('M', e.target.value)}
            style={{ width: '80px', marginTop: '5px' }}
          />
        </div>

        <div>
          <label><strong>Grande (L):</strong></label><br />
          <small>1.00 m³ | 150 kg</small><br />
          <input 
            type="number" 
            min="0" 
            value={cantidades.L} 
            onChange={(e) => handleChange('L', e.target.value)}
            style={{ width: '80px', marginTop: '5px' }}
          />
        </div>
      </div>

      <button 
        onClick={calcularCarga} 
        disabled={cargando}
        style={{
          padding: '10px 20px',
          background: '#0066cc',
          color: '#fff',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        {cargando ? 'Calculando...' : 'Calcular Carga'}
      </button>

      {resultado && (
        <div style={{ marginTop: '20px', borderTop: '1px solid #ccc', paddingTop: '15px' }}>
          <h4>Ocupación:</h4>
          <p>Volumen: <strong>{resultado.volumen_total_m3} m³</strong> ({resultado.alerta.porcentaje_m3}%)</p>
          <p>Peso: <strong>{resultado.peso_total_kg} kg</strong> ({resultado.alerta.porcentaje_kg}%)</p>

          <div style={{
            padding: '12px',
            borderRadius: '5px',
            color: '#fff',
            fontWeight: 'bold',
            background: resultado.alerta.nivel === 'CRITICO' ? '#d9534f' :
                        resultado.alerta.nivel === 'ADVERTENCIA' ? '#f0ad4e' : '#5cb85c'
          }}>
            {resultado.alerta.mensaje}
          </div>
        </div>
      )}
    </div>
  );
}