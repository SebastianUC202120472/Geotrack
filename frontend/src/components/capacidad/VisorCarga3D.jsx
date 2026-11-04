import { useEffect, useRef, useState } from "react";
import { Box, MousePointer2 } from "lucide-react";

// Colores de las cajas de carga (azul de marca + ámbar de acento).
const PALETA = [0x2563eb, 0x3b82f6, 0x60a5fa, 0xf59e0b, 0xfbbf24, 0x0ea5e9];

// Convierte un valor a número; 0 si no lo es. Recibe el valor.
const limpiarNumero = (valor) => (Number.isFinite(Number(valor)) ? Number(valor) : 0);

// Lleva el tipo del catálogo a una de las siluetas conocidas. Recibe el tipo.
const NORMALIZAR_TIPO = (tipo) => {
  if (!tipo) return "generico";
  const t = String(tipo).toLowerCase().trim();
  if (t.includes("camion_pesado") || t.includes("trailer") || t.includes("tracto")) return "camion_pesado";
  if (t.includes("camion_mediano")) return "camion_mediano";
  if (t.includes("camion_ligero") || t.includes("camion")) return "camion_ligero";
  if (t.includes("furgoneta") || t.includes("furgon")) return "furgoneta";
  if (t.includes("van")) return "van";
  if (t.includes("pickup") || t.includes("pick-up") || t.includes("camioneta")) return "pickup";
  if (t.includes("suv") || t.includes("4x4")) return "suv";
  if (t.includes("hatchback") || t.includes("compacto")) return "hatchback";
  if (t.includes("sedan") || t.includes("berlina") || t.includes("turismo")) return "sedan";
  return t;
};

const ETIQUETA_TIPO = {
  sedan: "Sedán",
  hatchback: "Hatchback",
  suv: "SUV",
  pickup: "Pickup",
  furgoneta: "Furgoneta",
  van: "Van",
  camion_ligero: "Camión ligero",
  camion_mediano: "Camión mediano",
  camion_pesado: "Camión pesado",
  generico: "Genérico",
};

// Vista lateral en SVG: se usa como respaldo cuando WebGL no está disponible o como fallback.
// Dibuja una silueta distinta por tipo para cumplir "un modelo por tipo".
function VistaLateral({ modelo, utilizacionPct = 0, mensaje }) {
  const fraccion = Math.min(1, Math.max(0, limpiarNumero(utilizacionPct) / 100));
  const cargaAncho = 205 * fraccion;
  const tipo = NORMALIZAR_TIPO(modelo?.tipo);
  const etiqueta = ETIQUETA_TIPO[tipo] || ETIQUETA_TIPO.generico;

  // Dibuja la silueta 2D del vehículo según su tipo. Sin parámetros.
  const renderSilueta = () => {
    if (tipo === "sedan") {
      return (
        <g>
          <rect x="30" y="48" width="170" height="38" rx="10" fill="#cbd5e1" />
          <path d="M40 48 h40 l12 -14 h50 l18 14 h40 v38 h-160 z" fill="#cbd5e1" />
          <rect x="58" y="38" width="34" height="10" rx="4" fill="#cbd5e1" />
          <rect x="130" y="38" width="34" height="10" rx="4" fill="#cbd5e1" />
          <circle cx="72" cy="88" r="9" fill="#334155" />
          <circle cx="198" cy="88" r="9" fill="#334155" />
        </g>
      );
    }
    if (tipo === "hatchback") {
      return (
        <g>
          <rect x="34" y="52" width="150" height="34" rx="8" fill="#cbd5e1" />
          <path d="M44 52 h38 l14 -16 h40 l16 16 h32 v34 h-140 z" fill="#cbd5e1" />
          <rect x="70" y="38" width="28" height="10" rx="3" fill="#cbd5e1" />
          <rect x="118" y="38" width="28" height="10" rx="3" fill="#cbd5e1" />
          <circle cx="78" cy="88" r="9" fill="#334155" />
          <circle cx="176" cy="88" r="9" fill="#334155" />
        </g>
      );
    }
    if (tipo === "suv") {
      return (
        <g>
          <rect x="28" y="44" width="176" height="44" rx="10" fill="#cbd5e1" />
          <path d="M38 44 h42 l16 -16 h56 l20 16 h42 v44 h-176 z" fill="#cbd5e1" />
          <rect x="70" y="30" width="32" height="12" rx="4" fill="#cbd5e1" />
          <rect x="126" y="30" width="32" height="12" rx="4" fill="#cbd5e1" />
          <circle cx="74" cy="90" r="10" fill="#334155" />
          <circle cx="196" cy="90" r="10" fill="#334155" />
        </g>
      );
    }
    if (tipo === "pickup") {
      return (
        <g>
          <rect x="18" y="46" width="110" height="42" rx="6" fill="#cbd5e1" />
          <rect x="132" y="52" width="110" height="36" rx="4" fill="#cbd5e1" />
          <path d="M28 46 h48 l10 -12 h36 l14 12 h32 v42 h-140 z" fill="#cbd5e1" />
          <circle cx="64" cy="90" r="10" fill="#334155" />
          <circle cx="170" cy="90" r="10" fill="#334155" />
          <circle cx="222" cy="90" r="10" fill="#334155" />
        </g>
      );
    }
    if (tipo === "furgoneta") {
      return (
        <g>
          <rect x="18" y="38" width="198" height="52" rx="8" fill="#cbd5e1" />
          <rect x="26" y="44" width="92" height="32" rx="4" fill="#cbd5e1" opacity="0.4" />
          <circle cx="68" cy="92" r="10" fill="#334155" />
          <circle cx="176" cy="92" r="10" fill="#334155" />
        </g>
      );
    }
    if (tipo === "van") {
      return (
        <g>
          <rect x="14" y="36" width="214" height="54" rx="10" fill="#cbd5e1" />
          <rect x="24" y="44" width="110" height="34" rx="4" fill="#cbd5e1" opacity="0.4" />
          <circle cx="72" cy="92" r="10" fill="#334155" />
          <circle cx="186" cy="92" r="10" fill="#334155" />
        </g>
      );
    }
    if (tipo === "camion_ligero") {
      return (
        <g>
          <rect x="16" y="42" width="118" height="46" rx="6" fill="#cbd5e1" />
          <rect x="138" y="48" width="124" height="40" rx="4" fill="#cbd5e1" />
          <path d="M26 42 h52 l12 -12 h38 l16 12 h36 v46 h-154 z" fill="#cbd5e1" />
          <circle cx="68" cy="90" r="10" fill="#334155" />
          <circle cx="184" cy="90" r="10" fill="#334155" />
          <circle cx="236" cy="90" r="10" fill="#334155" />
        </g>
      );
    }
    if (tipo === "camion_mediano") {
      return (
        <g>
          <rect x="12" y="38" width="126" height="50" rx="6" fill="#cbd5e1" />
          <rect x="142" y="44" width="142" height="44" rx="4" fill="#cbd5e1" />
          <path d="M22 38 h56 l14 -14 h42 l18 14 h38 v50 h-168 z" fill="#cbd5e1" />
          <circle cx="70" cy="90" r="11" fill="#334155" />
          <circle cx="192" cy="90" r="11" fill="#334155" />
          <circle cx="252" cy="90" r="11" fill="#334155" />
        </g>
      );
    }
    if (tipo === "camion_pesado") {
      return (
        <g>
          <rect x="10" y="36" width="130" height="52" rx="6" fill="#cbd5e1" />
          <rect x="144" y="40" width="156" height="48" rx="4" fill="#cbd5e1" />
          <path d="M20 36 h58 l16 -16 h46 l20 16 h40 v52 h-180 z" fill="#cbd5e1" />
          <circle cx="72" cy="90" r="12" fill="#334155" />
          <circle cx="198" cy="90" r="12" fill="#334155" />
          <circle cx="270" cy="90" r="12" fill="#334155" />
        </g>
      );
    }
    // Genérico: silueta tipo furgón
    return (
      <g>
        <rect x="20" y="42" width="230" height="48" rx="4" fill="#cbd5e1" />
        <path d="M250 58 h26 l16 22 v10 h-42 z" fill="#cbd5e1" />
        <circle cx="65" cy="94" r="9" fill="#334155" />
        <circle cx="225" cy="94" r="9" fill="#334155" />
        <circle cx="272" cy="94" r="8" fill="#475569" />
      </g>
    );
  };

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-slate-50 p-4">
      <svg viewBox="0 0 320 120" className="w-full max-w-md" role="img" aria-label={`Vista lateral de la carga - ${etiqueta}`}>
        {renderSilueta()}
        <rect x="40" y="58" width={cargaAncho} height="26" rx="3" fill="#3b82f6" opacity="0.75" />
        <line x1="20" y1="90" x2="292" y2="90" stroke="#94a3b8" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <p className="text-center text-xs text-slate-500">
        {mensaje || (modelo ? `Vista referencial (${etiqueta}) · ${utilizacionPct}%` : "Selecciona un viaje para ver la carga.")}
      </p>
    </div>
  );
}

// Visor 3D procedural por tipo de vehículo. Usa Three.js cargado bajo demanda.
// Renderiza solo al montar/cambiar (sin animación continua). Respaldo SVG si falla WebGL.
export default function VisorCarga3D({
  modelo,
  utilizacionPct = 0,
  placa = "",
  pedidos = 0,
  alto = 280,
}) {
  const contenedorRef = useRef(null);
  const [estado, setEstado] = useState("cargando");

  useEffect(() => {
    let cancelado = false;
    let limpiar = () => {};

    async function montar() {
      const contenedor = contenedorRef.current;
      if (!modelo || !contenedor) return;

      try {
        const THREE = await import("./piezasThree");
        if (cancelado || !contenedorRef.current) return;

        const largo = Math.max(0.5, limpiarNumero(modelo.largo_m) || 1);
        const profundo = Math.max(0.4, limpiarNumero(modelo.ancho_m) || 0.8);
        const altoCaja = Math.max(0.4, limpiarNumero(modelo.alto_m) || 0.8);
        const fraccion = Math.min(1, Math.max(0, limpiarNumero(utilizacionPct) / 100));
        const tipo = NORMALIZAR_TIPO(modelo.tipo);

        const anchoPx = contenedor.clientWidth || 480;
        const altoPx = alto;

        const escena = new THREE.Scene();
        const camara = new THREE.PerspectiveCamera(40, anchoPx / altoPx, 0.1, 200);
        camara.position.set(largo * 1.25, altoCaja * 1.9, Math.max(largo, profundo) * 2.4);
        camara.lookAt(0, altoCaja * 0.35, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(anchoPx, altoPx);
        renderer.domElement.style.width = "100%";
        renderer.domElement.style.height = "100%";
        renderer.domElement.style.display = "block";
        renderer.domElement.style.cursor = "grab";
        renderer.domElement.style.touchAction = "none";
        contenedor.appendChild(renderer.domElement);

        escena.add(new THREE.HemisphereLight(0xffffff, 0x94a3b8, 1.15));
        const luz = new THREE.DirectionalLight(0xffffff, 1.4);
        luz.position.set(largo, altoCaja * 3, profundo * 2);
        escena.add(luz);

        const grupo = new THREE.Group();
        escena.add(grupo);

        // Piso y grilla
        const piso = new THREE.Mesh(
          new THREE.PlaneGeometry(largo * 2.0, profundo * 2.6),
          new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 1 }),
        );
        piso.rotation.x = -Math.PI / 2;
        piso.position.y = 0.001;
        grupo.add(piso);

        const grilla = new THREE.GridHelper(Math.max(largo, profundo) * 1.8, 12, 0xe2e8f0, 0xe2e8f0);
        grilla.position.y = 0.004;
        grupo.add(grilla);

        // Silueta del vehículo por tipo (low-poly)
        const matCarroceria = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.8, metalness: 0.05 });
        const matCabina = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.8, metalness: 0.05 });
        const matRueda = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9, metalness: 0.0 });
        const matCristal = new THREE.MeshStandardMaterial({ color: 0x93c5fd, transparent: true, opacity: 0.25, roughness: 0.4 });

        // Agrega una rueda al modelo 3D. Recibe su posición x y z.
        const agregarRueda = (x, z) => {
          const rueda = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.12, 16), matRueda);
          rueda.rotation.x = Math.PI / 2;
          rueda.position.set(x, 0.16, z);
          grupo.add(rueda);
        };

        if (tipo === "sedan" || tipo === "hatchback") {
          const largoV = largo * 1.05;
          const profV = profundo * 0.95;
          const altoV = altoCaja * 0.55;
          const carro = new THREE.Mesh(new THREE.BoxGeometry(largoV, altoV, profV), matCarroceria);
          carro.position.set(0, altoV / 2 + 0.16, 0);
          grupo.add(carro);
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.58, altoV * 0.7, profV * 0.9), matCabina);
          cab.position.set(largoV * 0.02, altoV / 2 + 0.16 + altoV * 0.35, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.54, altoV * 0.5, profV * 0.92), matCristal);
          vidrio.position.set(largoV * 0.02, altoV / 2 + 0.16 + altoV * 0.38, 0);
          grupo.add(vidrio);
          agregarRueda(-largoV * 0.32, -profV * 0.42);
          agregarRueda(largoV * 0.32, -profV * 0.42);
          agregarRueda(-largoV * 0.32, profV * 0.42);
          agregarRueda(largoV * 0.32, profV * 0.42);
        } else if (tipo === "suv") {
          const largoV = largo * 1.08;
          const profV = profundo * 0.98;
          const altoV = altoCaja * 0.62;
          const carro = new THREE.Mesh(new THREE.BoxGeometry(largoV, altoV, profV), matCarroceria);
          carro.position.set(0, altoV / 2 + 0.18, 0);
          grupo.add(carro);
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.64, altoV * 0.72, profV * 0.92), matCabina);
          cab.position.set(largoV * 0.0, altoV / 2 + 0.18 + altoV * 0.36, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.6, altoV * 0.52, profV * 0.94), matCristal);
          vidrio.position.set(largoV * 0.0, altoV / 2 + 0.18 + altoV * 0.39, 0);
          grupo.add(vidrio);
          agregarRueda(-largoV * 0.34, -profV * 0.44);
          agregarRueda(largoV * 0.34, -profV * 0.44);
          agregarRueda(-largoV * 0.34, profV * 0.44);
          agregarRueda(largoV * 0.34, profV * 0.44);
        } else if (tipo === "pickup") {
          const largoV = largo * 1.1;
          const profV = profundo * 0.98;
          const altoCab = altoCaja * 0.58;
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.48, altoCab, profV * 0.92), matCabina);
          cab.position.set(-largoV * 0.24, altoCab / 2 + 0.18, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.44, altoCab * 0.5, profV * 0.94), matCristal);
          vidrio.position.set(-largoV * 0.24, altoCab / 2 + 0.18 + altoCab * 0.32, 0);
          grupo.add(vidrio);
          const caja = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.58, altoCaja * 0.48, profV * 0.94), matCarroceria);
          caja.position.set(largoV * 0.24, (altoCaja * 0.48) / 2 + 0.18, 0);
          grupo.add(caja);
          agregarRueda(-largoV * 0.34, -profV * 0.44);
          agregarRueda(largoV * 0.16, -profV * 0.44);
          agregarRueda(-largoV * 0.34, profV * 0.44);
          agregarRueda(largoV * 0.16, profV * 0.44);
        } else if (tipo === "furgoneta" || tipo === "van") {
          const largoV = largo * 1.16;
          const profV = profundo * 1.0;
          const altoV = altoCaja * 0.72;
          const carro = new THREE.Mesh(new THREE.BoxGeometry(largoV, altoV, profV), matCarroceria);
          carro.position.set(0, altoV / 2 + 0.18, 0);
          grupo.add(carro);
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.28, altoV * 0.62, profV * 0.9), matCabina);
          cab.position.set(-largoV * 0.34, altoV / 2 + 0.18 + altoV * 0.0, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.24, altoV * 0.38, profV * 0.92), matCristal);
          vidrio.position.set(-largoV * 0.34, altoV / 2 + 0.18 + altoV * 0.16, 0);
          grupo.add(vidrio);
          agregarRueda(-largoV * 0.38, -profV * 0.46);
          agregarRueda(largoV * 0.24, -profV * 0.46);
          agregarRueda(-largoV * 0.38, profV * 0.46);
          agregarRueda(largoV * 0.24, profV * 0.46);
        } else if (tipo === "camion_ligero") {
          const largoV = largo * 1.24;
          const profV = profundo * 1.02;
          const altoCab = altoCaja * 0.66;
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.26, altoCab, profV * 0.9), matCabina);
          cab.position.set(-largoV * 0.36, altoCab / 2 + 0.2, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.22, altoCab * 0.36, profV * 0.92), matCristal);
          vidrio.position.set(-largoV * 0.36, altoCab / 2 + 0.2 + altoCab * 0.16, 0);
          grupo.add(vidrio);
          const caja = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.72, altoCaja * 0.56, profV * 0.96), matCarroceria);
          caja.position.set(largoV * 0.12, (altoCaja * 0.56) / 2 + 0.2, 0);
          grupo.add(caja);
          agregarRueda(-largoV * 0.4, -profV * 0.48);
          agregarRueda(largoV * 0.22, -profV * 0.48);
          agregarRueda(-largoV * 0.4, profV * 0.48);
          agregarRueda(largoV * 0.22, profV * 0.48);
        } else if (tipo === "camion_mediano") {
          const largoV = largo * 1.32;
          const profV = profundo * 1.04;
          const altoCab = altoCaja * 0.7;
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.24, altoCab, profV * 0.9), matCabina);
          cab.position.set(-largoV * 0.38, altoCab / 2 + 0.22, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.2, altoCab * 0.34, profV * 0.92), matCristal);
          vidrio.position.set(-largoV * 0.38, altoCab / 2 + 0.22 + altoCab * 0.16, 0);
          grupo.add(vidrio);
          const caja = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.74, altoCaja * 0.6, profV * 0.98), matCarroceria);
          caja.position.set(largoV * 0.12, (altoCaja * 0.6) / 2 + 0.22, 0);
          grupo.add(caja);
          agregarRueda(-largoV * 0.42, -profV * 0.5);
          agregarRueda(largoV * 0.26, -profV * 0.5);
          agregarRueda(-largoV * 0.42, profV * 0.5);
          agregarRueda(largoV * 0.26, profV * 0.5);
        } else if (tipo === "camion_pesado") {
          const largoV = largo * 1.38;
          const profV = profundo * 1.06;
          const altoCab = altoCaja * 0.72;
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.22, altoCab, profV * 0.9), matCabina);
          cab.position.set(-largoV * 0.4, altoCab / 2 + 0.24, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.18, altoCab * 0.32, profV * 0.92), matCristal);
          vidrio.position.set(-largoV * 0.4, altoCab / 2 + 0.24 + altoCab * 0.16, 0);
          grupo.add(vidrio);
          const caja = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.76, altoCaja * 0.64, profV * 1.0), matCarroceria);
          caja.position.set(largoV * 0.12, (altoCaja * 0.64) / 2 + 0.24, 0);
          grupo.add(caja);
          agregarRueda(-largoV * 0.44, -profV * 0.52);
          agregarRueda(largoV * 0.3, -profV * 0.52);
          agregarRueda(-largoV * 0.44, profV * 0.52);
          agregarRueda(largoV * 0.3, profV * 0.52);
        } else {
          // Genérico
          const largoV = largo * 1.12;
          const profV = profundo * 0.98;
          const altoV = altoCaja * 0.6;
          const carro = new THREE.Mesh(new THREE.BoxGeometry(largoV, altoV, profV), matCarroceria);
          carro.position.set(0, altoV / 2 + 0.18, 0);
          grupo.add(carro);
          const cab = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.32, altoV * 0.6, profV * 0.9), matCabina);
          cab.position.set(-largoV * 0.34, altoV / 2 + 0.18 + altoV * 0.0, 0);
          grupo.add(cab);
          const vidrio = new THREE.Mesh(new THREE.BoxGeometry(largoV * 0.28, altoV * 0.36, profV * 0.92), matCristal);
          vidrio.position.set(-largoV * 0.34, altoV / 2 + 0.18 + altoV * 0.14, 0);
          grupo.add(vidrio);
          agregarRueda(-largoV * 0.38, -profV * 0.46);
          agregarRueda(largoV * 0.22, -profV * 0.46);
          agregarRueda(-largoV * 0.38, profV * 0.46);
          agregarRueda(largoV * 0.22, profV * 0.46);
        }

        // Caja del vehículo: volumen útil disponible (transparente)
        const geometriaCaja = new THREE.BoxGeometry(largo, altoCaja, profundo);
        const relleno = new THREE.Mesh(
          geometriaCaja,
          new THREE.MeshStandardMaterial({
            color: 0xdbeafe,
            transparent: true,
            opacity: 0.18,
            depthWrite: false,
          }),
        );
        relleno.position.y = altoCaja / 2;
        grupo.add(relleno);

        const aristas = new THREE.LineSegments(
          new THREE.EdgesGeometry(geometriaCaja),
          new THREE.LineBasicMaterial({ color: 0x64748b }),
        );
        aristas.position.y = altoCaja / 2;
        grupo.add(aristas);

        // Carga: grilla de cajas que ocupa la fracción utilizada
        let nx = Math.max(1, Math.floor((largo * fraccion) / 0.45));
        let ny = Math.max(1, Math.floor(altoCaja / 0.45));
        let nz = Math.max(1, Math.floor(profundo / 0.45));
        while (nx * ny * nz > 320) {
          if (nx >= ny && nx >= nz) nx -= 1;
          else if (ny >= nz) ny -= 1;
          else nz -= 1;
        }

        const pasoX = (largo * fraccion) / nx;
        const pasoY = altoCaja / ny;
        const pasoZ = profundo / nz;
        const geometriaCarga = new THREE.BoxGeometry(
          Math.max(0.05, pasoX * 0.84),
          Math.max(0.05, pasoY * 0.84),
          Math.max(0.05, pasoZ * 0.84),
        );
        const materiales = PALETA.map(
          (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.05 }),
        );

        let indice = 0;
        for (let ix = 0; fraccion > 0 && ix < nx; ix += 1) {
          for (let iy = 0; iy < ny; iy += 1) {
            for (let iz = 0; iz < nz; iz += 1) {
              const caja = new THREE.Mesh(geometriaCarga, materiales[indice % materiales.length]);
              caja.position.set(
                -largo / 2 + pasoX * (ix + 0.5),
                pasoY * (iy + 0.5),
                -profundo / 2 + pasoZ * (iz + 0.5),
              );
              grupo.add(caja);
              indice += 1;
            }
          }
        }

        // Rotación por arrastre y zoom con rueda; se dibuja solo al interactuar/cambiar
        const rotacion = { x: -0.4, y: 0.65 };
        grupo.rotation.set(rotacion.x, rotacion.y, 0);
        let arrastrando = false;
        let anterior = { x: 0, y: 0 };

        // Redibuja la escena una vez (no hay animación continua). Sin parámetros.
        const dibujar = () => renderer.render(escena, camara);
        dibujar();

        // Empieza a girar el modelo al presionar. Recibe el evento del puntero.
        const alPresionar = (evento) => {
          arrastrando = true;
          anterior = { x: evento.clientX, y: evento.clientY };
          if (renderer.domElement) renderer.domElement.style.cursor = "grabbing";
        };
        // Gira el modelo mientras se arrastra. Recibe el evento del puntero.
        const alMover = (evento) => {
          if (!arrastrando) return;
          const dx = evento.clientX - anterior.x;
          const dy = evento.clientY - anterior.y;
          rotacion.y += dx * 0.01;
          rotacion.x = Math.min(0.2, Math.max(-1.15, rotacion.x + dy * 0.01));
          grupo.rotation.set(rotacion.x, rotacion.y, 0);
          anterior = { x: evento.clientX, y: evento.clientY };
          dibujar();
        };
        // Termina el giro al soltar. Sin parámetros.
        const alSoltar = () => {
          arrastrando = false;
          if (renderer.domElement) renderer.domElement.style.cursor = "grab";
        };
        // Acerca o aleja la cámara con la rueda dentro de un rango. Recibe el evento de la rueda.
        const alRodar = (evento) => {
          evento.preventDefault();
          const factor = evento.deltaY > 0 ? 1.08 : 0.92;
          const nuevaPosicion = camara.position.clone().multiplyScalar(factor);
          const distanciaMinima = Math.max(largo, profundo, altoCaja) * 0.8;
          const distanciaMaxima = Math.max(largo, profundo, altoCaja) * 8;
          const distancia = nuevaPosicion.length();
          if (distancia >= distanciaMinima && distancia <= distanciaMaxima) {
            camara.position.copy(nuevaPosicion);
            camara.lookAt(0, altoCaja * 0.35, 0);
            dibujar();
          }
        };

        renderer.domElement.addEventListener("pointerdown", alPresionar);
        window.addEventListener("pointermove", alMover);
        window.addEventListener("pointerup", alSoltar);
        renderer.domElement.addEventListener("wheel", alRodar, { passive: false });

        const observador = new ResizeObserver(() => {
          const nuevoAncho = contenedor.clientWidth || anchoPx;
          camara.aspect = nuevoAncho / altoPx;
          camara.updateProjectionMatrix();
          renderer.setSize(nuevoAncho, altoPx);
          dibujar();
        });
        observador.observe(contenedor);

        limpiar = () => {
          observador.disconnect();
          renderer.domElement.removeEventListener("pointerdown", alPresionar);
          window.removeEventListener("pointermove", alMover);
          window.removeEventListener("pointerup", alSoltar);
          renderer.domElement.removeEventListener("wheel", alRodar);
          escena.traverse((objeto) => {
            if (objeto.geometry) objeto.geometry.dispose();
            if (Array.isArray(objeto.material)) {
              objeto.material.forEach((material) => material.dispose());
            } else if (objeto.material) {
              objeto.material.dispose();
            }
          });
          renderer.dispose();
          if (renderer.domElement && renderer.domElement.parentNode) {
            renderer.domElement.parentNode.removeChild(renderer.domElement);
          }
        };

        if (!cancelado) setEstado("listo");
      } catch {
        if (!cancelado) setEstado("error");
      }
    }

    montar();

    return () => {
      cancelado = true;
      limpiar();
    };
  }, [modelo, utilizacionPct, alto]);

  if (!modelo) {
    return <VistaLateral modelo={null} mensaje="Selecciona un viaje para ver cómo queda la carga." />;
  }

  if (estado === "error") {
    return (
      <VistaLateral
        modelo={modelo}
        utilizacionPct={utilizacionPct}
        mensaje={`Vista 2D de respaldo: este navegador no tiene WebGL activo. ${placa ? `Placa ${placa}.` : ""}`}
      />
    );
  }

  const tipo = NORMALIZAR_TIPO(modelo?.tipo);
  const etiquetaTipo = ETIQUETA_TIPO[tipo] || ETIQUETA_TIPO.generico;

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white">
      <div ref={contenedorRef} className="w-full" style={{ height: alto }} />

      {estado === "cargando" && (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-400">
          Preparando visor 3D...
        </div>
      )}

      <div className="pointer-events-none absolute left-3 top-3 rounded-lg bg-white/90 px-3 py-2 text-xs shadow-sm">
        <p className="flex items-center gap-1.5 font-semibold text-slate-700">
          <Box size={14} className="text-brand-600" />
          {placa || "Vista de carga"}
        </p>
        <p className="mt-0.5 text-slate-500">
          {modelo.marca} {modelo.modelo} · {etiquetaTipo}
        </p>
        <p className="text-slate-500">
          {utilizacionPct}% del volumen útil{pedidos ? ` · ${pedidos} pedidos` : ""}
        </p>
      </div>

      <div className="pointer-events-none absolute bottom-2 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-white/85 px-3 py-1 text-[11px] text-slate-500 shadow-sm">
        <MousePointer2 size={12} />
        Arrastra para girar · rueda para acercar
      </div>
    </div>
  );
}
