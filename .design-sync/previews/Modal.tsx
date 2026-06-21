// Preview del modal: confirmación centrada (estado abierto). Se renderiza con
// open dentro de la tarjeta (cfg.overrides.Modal usa cardMode single + viewport).
//
// Nota: la variante variant="right" (panel lateral deslizante) también existe
// y está documentada en Modal.d.ts; no se previsualiza porque su animación de
// entrada y su posición al borde derecho no se capturan de forma fiable en una
// tarjeta estática (ver .design-sync/NOTES.md).
import { Modal, Button } from "frontend-geotrack";

const noop = () => {};

export const Centrado = () => (
  <Modal open onClose={noop} variant="center">
    <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 700, color: "#0f172a" }}>
      Eliminar conductor
    </h2>
    <p style={{ margin: "0 0 20px", color: "#475569", fontSize: 14, lineHeight: 1.5 }}>
      ¿Seguro que deseas eliminar a Juan Pérez? Se liberará su vehículo asignado.
    </p>
    <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
      <Button variant="ghost" size="sm">Cancelar</Button>
      <Button variant="danger" size="sm">Eliminar</Button>
    </div>
  </Modal>
);
