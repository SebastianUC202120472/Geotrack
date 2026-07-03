import { useEffect, useRef } from 'react';
import { armarEscena, pintarEscena } from './escenaIso';

// Textos por defecto del HUD (español), uno por cada estado del recorrido.
// enRuta(n,total) camino a la siguiente entrega; cercaDe(n,total,nombre) al
// acercarse a una parada; completada(total) al terminar la ruta.
const TEXTOS_DEFECTO = {
  enRuta: (n, total) => 'En ruta a la entrega ' + n + ' de ' + total,
  cercaDe: (n, total, nombre) => 'Entregando pedido ' + n + ' de ' + total + ' · ' + nombre,
  completada: (total) => 'Ruta completada · ' + total + ' pedidos entregados ✓',
  vivo: 'EN VIVO',
  hint: 'Gire el mapa arrastrándolo · lleve la camioneta para adelantar la ruta',
};

// MapaHeroIso: mapa isométrico del hero. La camioneta recorre la ruta sola (rAF),
// se puede arrastrar el mapa para girar la cámara y arrastrar la camioneta para
// adelantar/retroceder. Prop opcional `textos` con { enRuta, cercaDe, completada,
// vivo, hint } para el HUD bilingüe (Landing/Hero inyecta el i18n).
export default function MapaHeroIso({ textos }) {
  const svgRef = useRef(null);

  // Toda la animación es manipulación directa del DOM/SVG vía ref (sin setState),
  // igual que setupMapa() del mockup. Un solo useEffect monta y limpia todo.
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const ruta = svg.querySelector('#rutaMapa');
    const prog = svg.querySelector('#rutaProg');
    const van = svg.querySelector('#vanMapa');
    const hud = svg.querySelector('#hudMapa');
    if (!ruta || !prog || !van) return;
    const enRuta = (textos && textos.enRuta) || TEXTOS_DEFECTO.enRuta;
    const cercaDe = (textos && textos.cercaDe) || TEXTOS_DEFECTO.cercaDe;
    const completada = (textos && textos.completada) || TEXTOS_DEFECTO.completada;

    const L = ruta.getTotalLength();
    prog.setAttribute('stroke-dasharray', String(L));

    // Escena 3D con cámara orbitable (arrastrar el mapa gira e inclina la vista)
    const escena = armarEscena(svg, '', () => pintarEscena(svg, '', escena.camara));

    // Longitud sobre la ruta de cada parada (su punto más cercano a la curva)
    const paradas = Array.from(svg.querySelectorAll('[data-parada]')).map(c => {
      const px = parseFloat(c.getAttribute('cx')), py = parseFloat(c.getAttribute('cy'));
      let best = 0, bd = Infinity;
      for (let i = 0; i <= 500; i++) {
        const l = L * i / 500, p = ruta.getPointAtLength(l);
        const d = (p.x - px) * (p.x - px) + (p.y - py) * (p.y - py);
        if (d < bd) { bd = d; best = l; }
      }
      return { el: c, len: best, nombre: c.dataset.parada };
    }).sort((a, b) => a.len - b.len);

    // Convierte coordenadas de pantalla a coordenadas del SVG (para arrastrar la van)
    const toSvg = (e) => { const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; return pt.matrixTransform(ruta.getScreenCTM().inverse()); };

    // Estado local del recorrido (antes global window.__savaVanLen en el mockup)
    let vanLen = 0;
    let arrastrandoVan = false;

    // Arrastre de la camioneta: engancha el punto de la ruta más cercano al cursor
    const onVanDown = (e) => { arrastrandoVan = true; van.style.cursor = 'grabbing'; van.setPointerCapture(e.pointerId); e.preventDefault(); };
    const onVanMove = (e) => {
      if (!arrastrandoVan) return;
      const m = toSvg(e);
      let best = vanLen, bd = Infinity;
      for (let i = 0; i <= 700; i++) {
        const l = L * i / 700, p = ruta.getPointAtLength(l);
        const d = (p.x - m.x) * (p.x - m.x) + (p.y - m.y) * (p.y - m.y);
        if (d < bd) { bd = d; best = l; }
      }
      vanLen = best;
    };
    const finVan = () => { arrastrandoVan = false; van.style.cursor = 'grab'; };
    van.addEventListener('pointerdown', onVanDown);
    van.addEventListener('pointermove', onVanMove);
    van.addEventListener('pointerup', finVan);
    van.addEventListener('pointercancel', finVan);

    let last = performance.now(), pausa = 0, raf = 0;
    const paso = (t) => {
      const dt = Math.min(50, t - last); last = t;
      // Avanza sola salvo mientras el usuario arrastra la camioneta
      if (!arrastrandoVan) {
        if (pausa > 0) { pausa -= dt; }
        else {
          vanLen += dt * 0.075;
          if (vanLen > L + 1) { vanLen = 0; pausa = 1200; }
        }
      }
      const l = Math.max(0, Math.min(L, vanLen));
      const p = ruta.getPointAtLength(l);
      const p2 = ruta.getPointAtLength(Math.min(L, l + 2));
      const ang = Math.atan2(p2.y - p.y, p2.x - p.x) * 180 / Math.PI;
      van.setAttribute('transform', 'translate(' + p.x + ' ' + p.y + ') rotate(' + ang + ')');
      prog.setAttribute('stroke-dashoffset', String(L - l));
      // Paradas: blanco (pendiente) → azul (cerca) → verde (pasada)
      let idx = 0, cerca = null, cercaN = 0;
      paradas.forEach((s, i) => {
        const esCerca = Math.abs(s.len - l) < 16;
        const pasada = l > s.len + 12;
        s.el.setAttribute('fill', pasada ? '#22a35e' : (esCerca ? '#2679d8' : '#fff'));
        s.el.setAttribute('stroke', pasada ? '#22a35e' : '#2679d8');
        s.el.setAttribute('r', esCerca ? '10' : '7');
        if (l >= s.len - 6) idx = i + 1;
        if (esCerca) { cerca = s; cercaN = i + 1; }
      });
      if (hud) {
        const total = paradas.length;
        if (l >= L - 4) hud.textContent = completada(total);
        else if (cerca) hud.textContent = cercaDe(cercaN, total, cerca.nombre);
        else {
          const sig = Math.min(total, idx + 1);
          hud.textContent = enRuta(sig, total);
        }
      }
      raf = requestAnimationFrame(paso);
    };
    raf = requestAnimationFrame(paso);

    // Limpieza total al desmontar: corta el rAF y desconecta cámara + camioneta
    return () => {
      cancelAnimationFrame(raf);
      van.removeEventListener('pointerdown', onVanDown);
      van.removeEventListener('pointermove', onVanMove);
      van.removeEventListener('pointerup', finVan);
      van.removeEventListener('pointercancel', finVan);
      escena.limpiar();
    };
  }, [textos]);

  // Texto inicial del HUD (antes del primer frame del rAF); 7 = total de paradas fijas del SVG.
  const enRutaInicial = ((textos && textos.enRuta) || TEXTOS_DEFECTO.enRuta)(1, 7);

  return (
    <div style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        id="svgMapa"
        viewBox="0 0 1135 700"
        style={{ width: '100%', height: 'auto', display: 'block', touchAction: 'none', cursor: 'grab', filter: 'drop-shadow(0 36px 54px rgba(2,12,26,.55))' }}
        aria-label="Mapa 3D de reparto en vivo — arrastre para girar la vista"
      >
        <g id="isoPlano" transform="matrix(0.707 0.389 -0.707 0.389 560 120)">
          <rect x="-18" y="-18" width="796" height="556" rx="26" fill="#eef4fa" stroke="#ffffff" strokeWidth="4" />
          <g id="manzanas" fill="#dde9f4">
            <rect x="30" y="30" width="110" height="80" rx="7" /><rect x="170" y="30" width="170" height="80" rx="7" /><rect x="380" y="30" width="120" height="80" rx="7" /><rect x="540" y="30" width="190" height="80" rx="7" />
            <rect x="30" y="150" width="110" height="90" rx="7" /><rect x="170" y="150" width="170" height="90" rx="7" /><rect x="380" y="150" width="120" height="90" rx="7" fill="#d8ecdc" /><rect x="540" y="150" width="190" height="90" rx="7" />
            <rect x="30" y="280" width="110" height="80" rx="7" /><rect x="170" y="280" width="170" height="80" rx="7" /><rect x="380" y="280" width="120" height="80" rx="7" /><rect x="540" y="280" width="190" height="80" rx="7" />
            <rect x="30" y="400" width="110" height="60" rx="7" /><rect x="170" y="400" width="170" height="60" rx="7" /><rect x="380" y="400" width="120" height="60" rx="7" /><rect x="540" y="400" width="190" height="60" rx="7" />
          </g>
          <path id="rutaMapa" d="M 60 130 L 360 130 L 360 260 L 160 260 L 160 380 L 520 380 L 520 480 L 690 480" fill="none" stroke="#c9dcee" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
          <path id="rutaProg" d="M 60 130 L 360 130 L 360 260 L 160 260 L 160 380 L 520 380 L 520 480 L 690 480" fill="none" stroke="#2679d8" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="4000" strokeDashoffset="4000" />
          <g>
            <circle data-parada="Av. Carlos Izaguirre" cx="210" cy="130" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-parada="Av. Túpac Amaru" cx="360" cy="200" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-parada="Av. Universitaria" cx="270" cy="260" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-parada="Av. Los Alisos" cx="160" cy="320" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-parada="Av. Antúnez de Mayolo" cx="300" cy="380" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-parada="Av. Naranjal" cx="520" cy="430" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
          </g>
          <g>
            <circle cx="52" cy="130" r="22" fill="#2679d8" opacity=".15" style={{ transformBox: 'fill-box', transformOrigin: 'center', animation: 'pulso 2.6s ease-out infinite' }} />
            <circle cx="52" cy="130" r="13" fill="#0f2b4a" stroke="#fff" strokeWidth="3" />
            <circle cx="52" cy="130" r="4" fill="#5db1f0" />
          </g>
          <g>
            <circle data-parada="Calle Los Nogales" cx="690" cy="480" r="7" fill="#fff" stroke="#2679d8" strokeWidth="3" />
          </g>
          <g id="edificios" style={{ pointerEvents: 'none' }}></g>
          <g id="vanMapa" style={{ cursor: 'grab' }}>
            <circle r="24" fill="#2679d8" opacity=".15" />
            <rect x="-17" y="-11" width="34" height="22" rx="6" fill="#0f2b4a" />
            <rect x="-14" y="-8" width="17" height="16" rx="3" fill="#274a70" />
            <rect x="6" y="-9" width="9" height="18" rx="2.5" fill="#5db1f0" />
          </g>
        </g>
        <text data-i18n="mapSava" data-world="52,130,-32" x="392" y="122" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '16px', fontWeight: 700, fill: '#0f2b4a', paintOrder: 'stroke', stroke: '#eef4fa', strokeWidth: '5px' }}>{(textos && textos.mapSava) || 'Centro SAVA'}</text>
      </svg>
      <div style={{ position: 'absolute', top: '10px', left: '6%', display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,.93)', backdropFilter: 'blur(8px)', border: '1px solid rgba(15,43,74,.08)', borderRadius: '99px', padding: '9px 16px', boxShadow: '0 10px 26px rgba(3,15,30,.28)', pointerEvents: 'none' }}>
        <span style={{ width: '9px', height: '9px', borderRadius: '99px', background: '#22a35e', animation: 'latido 1.8s ease-in-out infinite' }}></span>
        <span id="hudMapa" style={{ fontSize: '13px', fontWeight: 600, color: '#0f2b4a', whiteSpace: 'nowrap' }}>{enRutaInicial}</span>
        <span data-i18n="mapVivo" style={{ background: '#e3f2e8', color: '#1e7a43', fontSize: '10.5px', fontWeight: 700, letterSpacing: '.06em', padding: '3px 9px', borderRadius: '99px' }}>{(textos && textos.vivo) || TEXTOS_DEFECTO.vivo}</span>
      </div>
      <p data-i18n="mapHint" style={{ position: 'absolute', bottom: '6px', left: '50%', transform: 'translateX(-50%)', margin: 0, whiteSpace: 'nowrap', fontSize: '12px', color: '#dbe9f8', background: 'rgba(10,30,54,.62)', backdropFilter: 'blur(6px)', borderRadius: '99px', padding: '8px 16px', pointerEvents: 'none' }}>{(textos && textos.hint) || TEXTOS_DEFECTO.hint}</p>
    </div>
  );
}
