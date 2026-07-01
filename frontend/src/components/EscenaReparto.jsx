// Tile: bloque SVG de barrio repetido para el scroll infinito. Sin props.
const Tile = () => (
  <svg width="380" height="96" viewBox="0 0 380 96">
    <g opacity="0.9">
      <polygon points="8,52 42,26 76,52" fill="#566273" />
      <rect x="16" y="52" width="52" height="44" fill="#aab6c6" />
      <rect x="24" y="60" width="12" height="12" fill="#fbbf24" style={{ animation: "window-twinkle 3.4s ease-in-out infinite" }} />
      <rect x="46" y="72" width="14" height="24" fill="#6b7685" />
      <rect x="64" y="84" width="12" height="12" rx="1.5" fill="#d8a24a" />
      <line x1="70" y1="84" x2="70" y2="96" stroke="#00000033" strokeWidth="1.5" />
      <line x1="64" y1="89" x2="76" y2="89" stroke="#00000033" strokeWidth="1.5" />
      <polygon points="100,40 138,16 176,40" fill="#4c5868" />
      <rect x="108" y="40" width="60" height="56" fill="#9fabbc" />
      <rect x="116" y="50" width="12" height="12" fill="#fbbf24" style={{ animation: "window-twinkle 3.4s ease-in-out infinite .8s" }} />
      <rect x="146" y="50" width="12" height="12" fill="#fbbf24" style={{ animation: "window-twinkle 3.4s ease-in-out infinite .4s" }} />
      <rect x="132" y="70" width="14" height="26" fill="#6b7685" />
      <polygon points="206,56 238,32 270,56" fill="#566273" />
      <rect x="214" y="56" width="48" height="40" fill="#aab6c6" />
      <rect x="222" y="64" width="11" height="11" fill="#fbbf24" style={{ animation: "window-twinkle 3.4s ease-in-out infinite 1.2s" }} />
      <rect x="242" y="74" width="13" height="22" fill="#6b7685" />
      <rect x="258" y="85" width="11" height="11" rx="1.5" fill="#d8a24a" />
      <line x1="263.5" y1="85" x2="263.5" y2="96" stroke="#00000033" strokeWidth="1.5" />
      <line x1="258" y1="90" x2="269" y2="90" stroke="#00000033" strokeWidth="1.5" />
      <polygon points="300,60 328,40 356,60" fill="#566273" />
      <rect x="308" y="60" width="40" height="36" fill="#aab6c6" />
      <rect x="315" y="68" width="10" height="10" fill="#fbbf24" style={{ animation: "window-twinkle 3.4s ease-in-out infinite 1.6s" }} />
      <rect x="333" y="76" width="12" height="20" fill="#6b7685" />
    </g>
  </svg>
);

// EscenaReparto: animacion de camion + barrio desplazandose para la pantalla de login. Sin props.
export default function EscenaReparto() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* barrio: 4 tiles idénticos, scroll exacto de 380px */}
      <div
        className="absolute bottom-[58px] left-0 flex"
        style={{ animation: "town-scroll 24s linear infinite", willChange: "transform" }}
      >
        <Tile /><Tile /><Tile /><Tile />
      </div>

      {/* carretera */}
      <div className="absolute inset-x-0 bottom-[46px] z-[2] h-3 bg-[#0c1118]" />
      <div
        className="absolute inset-x-0 bottom-[51px] z-[3] h-[3px] opacity-85"
        style={{
          background: "repeating-linear-gradient(90deg,#f59e0b 0 22px, transparent 22px 40px)",
          animation: "road-dash 1.7s linear infinite",
        }}
      />

      {/* camión */}
      <svg
        className="absolute bottom-[50px] left-[48%] z-[4]"
        width="124" height="60" viewBox="0 0 124 60"
        style={{ animation: "truck-bob 2.6s ease-in-out infinite" }}
      >
        <rect x="6" y="14" width="64" height="32" rx="3" fill="#ffffff" />
        <rect x="14" y="22" width="18" height="16" rx="2" fill="#f59e0b" />
        <line x1="23" y1="22" x2="23" y2="38" stroke="#00000026" strokeWidth="1.5" />
        <line x1="14" y1="30" x2="32" y2="30" stroke="#00000026" strokeWidth="1.5" />
        <path d="M70 14 h18 l12 14 v16 h-30 z" fill="#2563eb" />
        <rect x="76" y="20" width="16" height="11" rx="2" fill="#bfdbfe" />
        <rect x="98" y="40" width="4" height="4" rx="1" fill="#fde68a" />
        <g style={{ transformBox: "fill-box", transformOrigin: "center", animation: "wheel-spin 1.8s linear infinite" }}>
          <circle cx="28" cy="48" r="8.5" fill="#0f172a" /><circle cx="28" cy="48" r="3.2" fill="#64748b" />
          <rect x="27" y="40.5" width="2" height="15" fill="#334155" /><rect x="20.5" y="47" width="15" height="2" fill="#334155" />
        </g>
        <g style={{ transformBox: "fill-box", transformOrigin: "center", animation: "wheel-spin 1.8s linear infinite" }}>
          <circle cx="84" cy="48" r="8.5" fill="#0f172a" /><circle cx="84" cy="48" r="3.2" fill="#64748b" />
          <rect x="83" y="40.5" width="2" height="15" fill="#334155" /><rect x="76.5" y="47" width="15" height="2" fill="#334155" />
        </g>
      </svg>
    </div>
  );
}
