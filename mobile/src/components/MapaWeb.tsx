// Mapa de calles REAL dentro de la app, sin clave de Google: un WebView que
// carga Leaflet + OpenStreetMap (como el panel web) y dibuja la ruta encima
// (paradas numeradas + línea + la siguiente resaltada). Funciona en Expo Go.
import { StyleSheet, Text, View } from "react-native";
import { WebView } from "react-native-webview";
import { useTheme, fontSize, radius } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  paradas: ParadaManifiesto[]; // paradas (con lat/lng) de la ruta
  alto?: number; // alto del mapa en píxeles (por defecto 260)
}

// Punto que se inyecta al HTML del WebView.
interface PuntoWeb {
  lat: number;
  lng: number;
  sec: number;
  estado: string;
  dest: string;
  dir: string;
}

// Vuelve seguro el JSON de datos para incrustarlo dentro de un <script>: escapa
// "<" (evita cerrar la etiqueta) y los separadores de línea Unicode U+2028/U+2029
// (que romperían el literal del script). Recibe los puntos; devuelve un string JSON seguro.
function jsonSeguro(puntos: PuntoWeb[]): string {
  return JSON.stringify(puntos)
    .replace(/</g, "\\u003c")
    .split(String.fromCharCode(0x2028)).join("\\u2028")
    .split(String.fromCharCode(0x2029)).join("\\u2029");
}

// HTML con Leaflet + OSM. Los datos de la ruta se inyectan reemplazando __DATOS__.
function construirHtml(puntos: PuntoWeb[]): string {
  const datos = jsonSeguro(puntos);
  return `<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous"/>
<style>
html,body,#map{height:100%;margin:0;background:#e9eef4}
@keyframes latido{0%{transform:scale(1);opacity:.55}70%{transform:scale(2.2);opacity:0}100%{opacity:0}}
.parada-activa{overflow:visible!important}
.parada-activa::after{content:'';position:absolute;left:50%;top:50%;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;background:rgba(37,99,235,.5);animation:latido 1.8s ease-out infinite;z-index:-1}
</style>
</head><body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous"></script>
<script>
  var paradas = __DATOS__;
  // Escapa texto para mostrarlo en el popup como TEXTO, no como HTML (anti-XSS).
  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  var map = L.map('map', { zoomControl: true });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
  var pts = [], siguienteUsada = false;
  paradas.forEach(function (p, i) {
    if (p.lat == null || p.lng == null) return;
    var pendiente = p.estado === 'PENDIENTE';
    var esSiguiente = pendiente && !siguienteUsada; if (esSiguiente) siguienteUsada = true;
    var color = p.estado === 'ENTREGADO' ? '#16a34a' : p.estado === 'FALLIDO' ? '#dc2626' : (esSiguiente ? '#2563eb' : '#f59e0b');
    var size = esSiguiente ? 34 : 28;
    var icon = L.divIcon({
      className: esSiguiente ? 'parada-activa' : '',
      html: '<div style="background:' + color + ';width:' + size + 'px;height:' + size + 'px;border-radius:50%;border:2px solid #fff;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.3)">' + (p.sec || (i + 1)) + '</div>',
      iconSize: [size, size], iconAnchor: [size / 2, size / 2]
    });
    L.marker([p.lat, p.lng], { icon: icon }).addTo(map).bindPopup('<b>' + esc(p.dest || 'Parada') + '</b><br>' + esc(p.dir || ''));
    pts.push([p.lat, p.lng]);
  });
  if (pts.length > 1) { L.polyline(pts, { color: '#2563eb', weight: 4 }).addTo(map); map.fitBounds(pts, { padding: [40, 40] }); }
  else if (pts.length === 1) { map.setView(pts[0], 15); }
  else { map.setView([-12.046, -77.043], 12); }
</script>
</body></html>`.replace("__DATOS__", () => datos);
}

// Mapa de calles de la ruta. Recibe: { paradas, alto? }.
export function MapaWeb({ paradas, alto = 260 }: Props) {
  const { colors } = useTheme();

  const puntos: PuntoWeb[] = paradas
    .filter((p) => p.latitud != null && p.longitud != null)
    .slice()
    .sort((a, b) => a.secuencia - b.secuencia)
    .map((p) => ({
      lat: p.latitud as number,
      lng: p.longitud as number,
      sec: p.secuencia,
      estado: p.estado_entrega,
      dest: p.nombre_destinatario || p.cliente_origen,
      dir: p.direccion_destino,
    }));

  if (puntos.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Text style={{ color: colors.muted, textAlign: "center", fontSize: fontSize.body }}>
          Aún no hay paradas con ubicación para mostrar en el mapa.
        </Text>
      </View>
    );
  }

  return (
    <View style={[estilos.caja, { height: alto, borderColor: colors.border }]}>
      <WebView
        originWhitelist={["*"]}
        source={{ html: construirHtml(puntos) }}
        style={{ flex: 1, backgroundColor: "#e9eef4" }}
        scrollEnabled={false}
        // En Expo Go el mapa carga Leaflet/OSM desde internet (no necesita clave).
      />
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { borderRadius: radius.lg, borderWidth: 1, overflow: "hidden" },
  vacio: { borderRadius: radius.lg, borderWidth: 1, alignItems: "center", justifyContent: "center", padding: 16 },
});
