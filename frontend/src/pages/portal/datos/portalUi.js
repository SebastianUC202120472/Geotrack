// Catálogos de PRESENTACIÓN del portal (colores/textos/franjas). No son datos:
// se quedan en el frontend aunque los datos vengan del backend.

export const ESTADOS = {
  EN_RUTA: { tx: "EN RUTA", bg: "#e4effc", fg: "#1b5fb3", trazo: "#2679d8", barra: "linear-gradient(90deg,#2679d8,#5db1f0)" },
  ENTREGADO: { tx: "ENTREGADO", bg: "#e3f2e8", fg: "#1e7a43", trazo: "#22a35e", barra: "linear-gradient(90deg,#2679d8,#22a35e)" },
  REPROGRAMADO: { tx: "REPROGRAMADO", bg: "#fdeedd", fg: "#b35c12", trazo: "#d97a1f", barra: "linear-gradient(90deg,#2679d8,#d97a1f)" },
  POR_SALIR: { tx: "POR SALIR", bg: "#eef2f6", fg: "#52708e", trazo: "#7288a0", barra: "#9db3c9" },
  OBSERVADO: { tx: "OBSERVADO", bg: "#fdeedd", fg: "#b35c12", trazo: "#d97a1f", barra: "linear-gradient(90deg,#2679d8,#d97a1f)" },
  CANCELADO: { tx: "CANCELADO", bg: "#f1f0f2", fg: "#6b6470", trazo: "#9a92a3", barra: "#c9c2d0" },
};

export const OPCIONES = ["Mañana · 9 am – 1 pm", "Mañana · 2 pm – 6 pm", "Sábado · 9 am – 1 pm"];
