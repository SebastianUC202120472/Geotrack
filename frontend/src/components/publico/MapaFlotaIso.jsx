import { useEffect, useRef } from 'react';
import { armarEscena, pintarEscena } from './escenaIso';

// MapaFlotaIso: mapa isométrico de la flota SAVA. Tres camionetas recorren sus
// rutas a distinta velocidad, marcando clientes (verde) y lanzando un flash
// "Evidencia lista" en cada entrega. Cámara orbitable (sufijo de ids '2'). Sin props.
export default function MapaFlotaIso() {
  const svgRef = useRef(null);

  // Toda la animación es manipulación directa del DOM/SVG vía ref (sin setState),
  // igual que setupFlota() del mockup. Un solo useEffect monta y limpia todo.
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    // Escena 3D con cámara orbitable (sufijo '2')
    const escena = armarEscena(svg, '2', () => pintarEscena(svg, '2', escena.camara));

    // Prepara las 3 rutas: coloca cada cliente sobre su curva y guarda sus datos
    const rutas = [1, 2, 3].map(n => {
      const path = svg.querySelector('#rutaF' + n);
      const van = svg.querySelector('#vanF' + n);
      const flash = svg.querySelector('#flashF' + n);
      if (!path || !van) return null;
      const L = path.getTotalLength();
      const clis = Array.from(svg.querySelectorAll('[data-ruta="' + n + '"]')).map(c => {
        const len = parseFloat(c.dataset.frac) * L;
        const p = path.getPointAtLength(len);
        c.setAttribute('cx', p.x.toFixed(1));
        c.setAttribute('cy', p.y.toFixed(1));
        return { el: c, len };
      }).sort((a, b) => a.len - b.len);
      // len inicial escalonado por ruta; velocidad 0.05 + n*0.011 (px/ms)
      return { path, van, flash, L, clis, len: n * 0.11 * L, vel: 0.05 + n * 0.011, pausa: 0, flashT: 0, flashX: 0, flashY: 0 };
    }).filter(Boolean);
    if (!rutas.length) { return () => escena.limpiar(); }

    let last = performance.now(), raf = 0;
    const paso = (t) => {
      const dt = Math.min(50, t - last); last = t;
      rutas.forEach(r => {
        if (r.pausa > 0) { r.pausa -= dt; }
        else {
          const antes = r.len;
          r.len += dt * r.vel;
          // ¿Cruzó un cliente en este frame? Marca verde, pausa y prepara el flash
          const cli = r.clis.find(c => antes < c.len && r.len >= c.len);
          if (cli) {
            r.len = cli.len; r.pausa = 1050;
            cli.el.setAttribute('fill', '#22a35e');
            cli.el.setAttribute('stroke', '#22a35e');
            r.flashT = t;
            const p = r.path.getPointAtLength(cli.len);
            r.flashX = p.x; r.flashY = p.y;
          }
          // Al terminar la ruta, reinicia y limpia los clientes a blanco
          if (r.len > r.L + 40) {
            r.len = 0;
            r.clis.forEach(c => { c.el.setAttribute('fill', '#fff'); c.el.setAttribute('stroke', c.el.dataset.color || '#2679d8'); });
          }
        }
        const l = Math.max(0, Math.min(r.L, r.len));
        const p = r.path.getPointAtLength(l);
        const p2 = r.path.getPointAtLength(Math.min(r.L, l + 2));
        const ang = Math.atan2(p2.y - p.y, p2.x - p.x) * 180 / Math.PI;
        r.van.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ' ' + p.y.toFixed(1) + ') rotate(' + ang.toFixed(1) + ')');
        // Flash "Evidencia lista": aparece y sube; se proyecta con la matriz de cámara
        if (r.flash && r.flashT) {
          const k = (t - r.flashT) / 950;
          if (k >= 1) { r.flash.setAttribute('opacity', '0'); r.flashT = 0; }
          else {
            const m = (svg.__escenaMat || {})['2'];
            const fx = m ? m.a * r.flashX + m.c * r.flashY + m.e : r.flashX;
            const fy = m ? m.b * r.flashX + m.d * r.flashY + m.f : r.flashY;
            r.flash.setAttribute('transform', 'translate(' + fx.toFixed(1) + ' ' + (fy - 30 - k * 16).toFixed(1) + ')');
            r.flash.setAttribute('opacity', String((k < 0.15 ? k / 0.15 : 1 - Math.max(0, k - 0.55) / 0.45).toFixed(2)));
          }
        }
      });
      raf = requestAnimationFrame(paso);
    };
    raf = requestAnimationFrame(paso);

    // Limpieza total al desmontar: corta el rAF y desconecta la cámara
    return () => {
      cancelAnimationFrame(raf);
      escena.limpiar();
    };
  }, []);

  return (
    <div style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        id="svgFlota"
        viewBox="0 0 1240 720"
        style={{ width: '100%', height: 'auto', display: 'block', touchAction: 'none', cursor: 'grab', filter: 'drop-shadow(0 26px 40px rgba(9,40,75,.28))' }}
        aria-label="Mapa 3D de la flota SAVA por distritos — arrastre para girar"
      >
        <g id="isoPlano2" transform="matrix(0.707 0.389 -0.707 0.389 620 120)">
          <rect x="-18" y="-18" width="796" height="556" rx="26" fill="#eef4fa" stroke="#ffffff" strokeWidth="4" />
          <g>
            <rect x="30" y="30" width="220" height="220" fill="rgba(38,121,216,.055)" />
            <rect x="260" y="30" width="240" height="220" fill="rgba(34,163,94,.05)" />
            <rect x="510" y="30" width="220" height="220" fill="rgba(93,177,240,.07)" />
            <rect x="30" y="260" width="220" height="200" fill="rgba(34,163,94,.045)" />
            <rect x="260" y="260" width="240" height="200" fill="rgba(38,121,216,.05)" />
            <rect x="510" y="260" width="220" height="200" fill="rgba(93,177,240,.06)" />
            <path d="M 255 30 L 255 460 M 505 30 L 505 460 M 30 255 L 730 255" stroke="rgba(15,43,74,.14)" strokeWidth="1.5" strokeDasharray="6 7" fill="none" />
          </g>
          <g id="manzanas2" fill="#dde9f4">
            <rect x="30" y="30" width="110" height="80" rx="7" /><rect x="170" y="30" width="170" height="80" rx="7" /><rect x="380" y="30" width="120" height="80" rx="7" /><rect x="540" y="30" width="190" height="80" rx="7" />
            <rect x="30" y="150" width="110" height="90" rx="7" /><rect x="170" y="150" width="170" height="90" rx="7" /><rect x="380" y="150" width="120" height="90" rx="7" fill="#d8ecdc" /><rect x="540" y="150" width="190" height="90" rx="7" />
            <rect x="30" y="280" width="110" height="80" rx="7" /><rect x="170" y="280" width="170" height="80" rx="7" /><rect x="380" y="280" width="120" height="80" rx="7" /><rect x="540" y="280" width="190" height="80" rx="7" />
            <rect x="30" y="400" width="110" height="60" rx="7" /><rect x="170" y="400" width="170" height="60" rx="7" /><rect x="380" y="400" width="120" height="60" rx="7" /><rect x="540" y="400" width="190" height="60" rx="7" />
          </g>
          <path d="M 360 260 L 160 260 L 160 130 L 60 130" fill="none" stroke="#c9dcee" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M 360 260 L 360 130 L 520 130 L 520 260 L 700 260" fill="none" stroke="#c9dcee" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M 360 260 L 360 380 L 160 380 L 160 480 L 520 480" fill="none" stroke="#c9dcee" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
          <path id="rutaF1" d="M 360 260 L 160 260 L 160 130 L 60 130" fill="none" stroke="#2679d8" strokeWidth="4" strokeDasharray="8 12" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'dashflow 1.3s linear infinite' }} />
          <path id="rutaF2" d="M 360 260 L 360 130 L 520 130 L 520 260 L 700 260" fill="none" stroke="#5db1f0" strokeWidth="4" strokeDasharray="8 12" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'dashflow 1.5s linear infinite' }} />
          <path id="rutaF3" d="M 360 260 L 360 380 L 160 380 L 160 480 L 520 480" fill="none" stroke="#1b5fb3" strokeWidth="4" strokeDasharray="8 12" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'dashflow 1.4s linear infinite' }} />
          <g>
            <circle data-ruta="1" data-frac="0.3" data-color="#2679d8" r="6" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-ruta="1" data-frac="0.62" data-color="#2679d8" r="6" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-ruta="1" data-frac="0.92" data-color="#2679d8" r="6" fill="#fff" stroke="#2679d8" strokeWidth="3" />
            <circle data-ruta="2" data-frac="0.34" data-color="#5db1f0" r="6" fill="#fff" stroke="#5db1f0" strokeWidth="3" />
            <circle data-ruta="2" data-frac="0.66" data-color="#5db1f0" r="6" fill="#fff" stroke="#5db1f0" strokeWidth="3" />
            <circle data-ruta="2" data-frac="0.94" data-color="#5db1f0" r="6" fill="#fff" stroke="#5db1f0" strokeWidth="3" />
            <circle data-ruta="3" data-frac="0.28" data-color="#1b5fb3" r="6" fill="#fff" stroke="#1b5fb3" strokeWidth="3" />
            <circle data-ruta="3" data-frac="0.6" data-color="#1b5fb3" r="6" fill="#fff" stroke="#1b5fb3" strokeWidth="3" />
            <circle data-ruta="3" data-frac="0.9" data-color="#1b5fb3" r="6" fill="#fff" stroke="#1b5fb3" strokeWidth="3" />
          </g>
          <circle cx="360" cy="260" r="20" fill="#2679d8" opacity=".16" style={{ transformBox: 'fill-box', transformOrigin: 'center', animation: 'pulso 2.6s ease-out infinite' }} />
          <circle cx="360" cy="260" r="13" fill="#0f2b4a" stroke="#fff" strokeWidth="3" />
          <circle cx="360" cy="260" r="4" fill="#5db1f0" />
          <g id="edificios2"></g>
          <g id="vanF1"><rect x="-13" y="-8" width="26" height="16" rx="4" fill="#0f2b4a" /><rect x="5" y="-6" width="6" height="12" rx="2" fill="#2679d8" /></g>
          <g id="vanF2"><rect x="-13" y="-8" width="26" height="16" rx="4" fill="#0f2b4a" /><rect x="5" y="-6" width="6" height="12" rx="2" fill="#5db1f0" /></g>
          <g id="vanF3"><rect x="-13" y="-8" width="26" height="16" rx="4" fill="#0f2b4a" /><rect x="5" y="-6" width="6" height="12" rx="2" fill="#9cc4ec" /></g>
        </g>
        <text data-world="140,140,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>San Miguel</text>
        <text data-world="380,118,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>Magdalena</text>
        <text data-world="620,140,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>Jesús María</text>
        <text data-world="140,355,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>Pueblo Libre</text>
        <text data-world="380,415,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>Lince</text>
        <text data-world="620,355,-4" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '14px', fontWeight: 600, fill: '#52708e', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '4px' }}>San Isidro</text>
        <text data-world="360,260,-32" x="0" y="0" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '15px', fontWeight: 700, fill: '#0f2b4a', paintOrder: 'stroke', stroke: '#f0f6fb', strokeWidth: '5px' }}>Centro SAVA</text>
        <g id="flashF1" opacity="0" style={{ pointerEvents: 'none' }}><rect x="-56" y="-16" width="112" height="27" rx="13.5" fill="#0f2b4a" /><text x="0" y="3" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '12px', fontWeight: 700, fill: '#fff' }}>✓ Evidencia lista</text></g>
        <g id="flashF2" opacity="0" style={{ pointerEvents: 'none' }}><rect x="-56" y="-16" width="112" height="27" rx="13.5" fill="#0f2b4a" /><text x="0" y="3" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '12px', fontWeight: 700, fill: '#fff' }}>✓ Evidencia lista</text></g>
        <g id="flashF3" opacity="0" style={{ pointerEvents: 'none' }}><rect x="-56" y="-16" width="112" height="27" rx="13.5" fill="#0f2b4a" /><text x="0" y="3" textAnchor="middle" style={{ fontFamily: 'Inter,sans-serif', fontSize: '12px', fontWeight: 700, fill: '#fff' }}>✓ Evidencia lista</text></g>
      </svg>
      <div style={{ position: 'absolute', top: '14px', left: '14px', display: 'flex', alignItems: 'center', gap: '9px', background: 'rgba(255,255,255,.94)', backdropFilter: 'blur(6px)', border: '1px solid rgba(15,43,74,.08)', borderRadius: '99px', padding: '8px 15px', boxShadow: '0 8px 22px rgba(3,15,30,.14)', pointerEvents: 'none' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '99px', background: '#22a35e', animation: 'latido 1.8s ease-in-out infinite' }}></span>
        <span style={{ fontSize: '12.5px', fontWeight: 600, color: '#0f2b4a' }}>Flota SAVA en vivo · 3 conductores en ruta</span>
      </div>
    </div>
  );
}
