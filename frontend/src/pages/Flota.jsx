import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Polyline, Popup } from "react-leaflet";
import io from "socket.io-client";
import { getVehiculos } from "../services/api";

const socket = io(import.meta.env.VITE_WS_URL);

export default function FlotaTiempoReal() {

  const [vehiculos, setVehiculos] = useState([]);
  const [rutas, setRutas] = useState({});

  /* =========================
     CARGA INICIAL
  ========================= */
  useEffect(() => {
    const load = async () => {
      const data = await getVehiculos();
      setVehiculos(data.vehiculos || data);
    };

    load();
  }, []);

  /* =========================
     WEBSOCKET LIVE TRACKING
  ========================= */
  useEffect(() => {

    socket.on("vehiculo_update", (data) => {

      setVehiculos(prev =>
        prev.map(v =>
          v.id === data.vehiculo_id
            ? { ...v, lat: data.lat, lng: data.lng, estado: data.estado }
            : v
        )
      );

    });

    socket.on("ruta_update", (data) => {
      setRutas(prev => ({
        ...prev,
        [data.vehiculo_id]: data.paradas
      }));
    });

    return () => {
      socket.off("vehiculo_update");
      socket.off("ruta_update");
    };

  }, []);

  return (
    <div className="flex h-screen bg-slate-100">

      <main className="flex-1 p-6">

        <h1 className="text-3xl font-bold mb-4">
          Tracking Logístico en Tiempo Real
        </h1>

        <div className="bg-white rounded-xl border h-[600px]">

          <MapContainer
            center={[-12.05, -77.04]}
            zoom={13}
            style={{ height: "100%", width: "100%" }}
          >

            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

            {vehiculos.map(v => (
              <>
                {/* 🚚 VEHÍCULO */}
                <Marker key={v.id} position={[v.lat, v.lng]}>
                  <Popup>
                    <b>{v.codigo}</b><br />
                    Estado: {v.estado}
                  </Popup>
                </Marker>

                {/* 🧭 RUTA REAL */}
                {rutas[v.id] && (
                  <Polyline
                    positions={rutas[v.id]}
                    color="blue"
                  />
                )}
              </>
            ))}

          </MapContainer>

        </div>

      </main>
    </div>
  );
}