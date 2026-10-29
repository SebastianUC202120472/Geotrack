import { useEffect, useRef, useState } from "react";
import { Box, MousePointer2 } from "lucide-react";

// Colores de las cajas de carga (azul de marca + ambar de acento).
const PALETA = [0x2563eb, 0x3b82f6, 0x60a5fa, 0xf59e0b, 0xfbbf24, 0x0ea5e9];

const limpiarNumero = (valor) => (Number.isFinite(Number(valor)) ? Number(valor) : 0);

// Vista lateral en SVG: se usa como respaldo cuando WebGL no esta disponible.
// Recibe modelo, utilizacionPct y mensaje opcional.
function VistaLateral({ modelo, utilizacionPct = 0, mensaje }) {
  const fraccion = Math.min(1, Math.max(0.02, limpiarNumero(utilizacionPct) / 100));
  const cargaAncho = 230 * fraccion;

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-slate-50 p-4">
      <svg viewBox="0 0 320 120" className="w-full max-w-md" role="img" aria-label="Vista lateral de la carga">
        <rect x="20" y="42" width="230" height="48" rx="4" fill="#e2e8f0" />
        <rect x="22" y="44" width={cargaAncho} height="44" rx="3" fill="#3b82f6" opacity="0.85" />
        <path d="M250 58 h26 l16 22 v10 h-42 z" fill="#cbd5e1" />
        <circle cx="65" cy="94" r="9" fill="#334155" />
        <circle cx="225" cy="94" r="9" fill="#334155" />
        <circle cx="272" cy="94" r="8" fill="#475569" />
        <line x1="20" y1="90" x2="292" y2="90" stroke="#94a3b8" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <p className="text-center text-xs text-slate-500">
        {mensaje || (modelo ? "Vista referencial de la carga (sin WebGL)." : "Selecciona un viaje para ver la carga.")}
      </p>
    </div>
  );
}

// Visor 3D procedural de la carga. Usa Three.js cargado bajo demanda para no
// pesar en el bundle del panel. Recibe modelo, utilizacionPct, placa, pedidos y alto.
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

    // Monta la escena cuando el navegador tiene WebGL; si falla, cae al SVG.
    async function montar() {
      const contenedor = contenedorRef.current;
      if (!modelo || !contenedor) return;

      try {
        const THREE = await import("three");
        if (cancelado || !contenedorRef.current) return;

        const largo = Math.max(0.5, limpiarNumero(modelo.largo_m) || 1);
        const profundo = Math.max(0.4, limpiarNumero(modelo.ancho_m) || 0.8);
        const altoCaja = Math.max(0.4, limpiarNumero(modelo.alto_m) || 0.8);
        const fraccion = Math.min(1, Math.max(0.02, limpiarNumero(utilizacionPct) / 100));

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

        // Piso y grilla de referencia.
        const piso = new THREE.Mesh(
          new THREE.PlaneGeometry(largo * 1.8, profundo * 2.2),
          new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 1 }),
        );
        piso.rotation.x = -Math.PI / 2;
        piso.position.y = 0.001;
        grupo.add(piso);

        const grilla = new THREE.GridHelper(Math.max(largo, profundo) * 1.6, 10, 0xe2e8f0, 0xe2e8f0);
        grilla.position.y = 0.004;
        grupo.add(grilla);

        // Caja del vehiculo: volumen util disponible.
        const geometriaCaja = new THREE.BoxGeometry(largo, altoCaja, profundo);
        const relleno = new THREE.Mesh(
          geometriaCaja,
          new THREE.MeshStandardMaterial({
            color: 0xdbeafe,
            transparent: true,
            opacity: 0.2,
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

        // Carga: grilla de cajas que ocupa la fraccion utilizada del largo.
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
        for (let ix = 0; ix < nx; ix += 1) {
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

        // Rotacion por arrastre y zoom con la rueda; se dibuja solo al interactuar.
        const rotacion = { x: -0.4, y: 0.65 };
        grupo.rotation.set(rotacion.x, rotacion.y, 0);
        let arrastrando = false;
        let anterior = { x: 0, y: 0 };

        const dibujar = () => renderer.render(escena, camara);
        dibujar();

        const alPresionar = (evento) => {
          arrastrando = true;
          anterior = { x: evento.clientX, y: evento.clientY };
          renderer.domElement.style.cursor = "grabbing";
        };
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
        const alSoltar = () => {
          arrastrando = false;
          renderer.domElement.style.cursor = "grab";
        };
        const alRodar = (evento) => {
          evento.preventDefault();
          const factor = evento.deltaY > 0 ? 1.08 : 0.92;
          camara.position.multiplyScalar(factor);
          camara.lookAt(0, altoCaja * 0.35, 0);
          dibujar();
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
          renderer.domElement.remove();
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
    return <VistaLateral modelo={null} mensaje="Selecciona un viaje para ver como queda la carga." />;
  }

  if (estado === "error") {
    return <VistaLateral modelo={modelo} utilizacionPct={utilizacionPct} />;
  }

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
          {modelo.marca} {modelo.modelo}
        </p>
        <p className="text-slate-500">
          {utilizacionPct}% del volumen util
          {pedidos ? ` · ${pedidos} pedidos` : ""}
        </p>
      </div>

      <div className="pointer-events-none absolute bottom-2 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-white/85 px-3 py-1 text-[11px] text-slate-500 shadow-sm">
        <MousePointer2 size={12} />
        Arrastra para girar · rueda para acercar
      </div>
    </div>
  );
}