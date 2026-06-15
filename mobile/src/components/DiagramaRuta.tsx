// Diagrama de ruta SIN mapa de tiles: dibuja las paradas (en orden de secuencia)
// conectadas por la línea del recorrido, coloreadas por su estado, y resalta la
// siguiente parada pendiente. Siempre se ve (no depende de Google/OSM ni de claves).
import { Fragment } from "react";
import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Polyline, Text as SvgText } from "react-native-svg";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  paradas: ParadaManifiesto[]; // paradas (con lat/lng) de la ruta
  alto?: number; // alto del lienzo en píxeles (por defecto 220)
}

// Lienzo virtual donde se proyectan las coordenadas.
const W = 300;
const P = 26; // margen interno

// Proyecta lat/lng a coordenadas x,y del lienzo (norte hacia arriba). Si todos los
// puntos coinciden, los centra. Recibe: paradas con coords y el alto del lienzo.
function proyectar(paradas: ParadaManifiesto[], H: number) {
  const lats = paradas.map((p) => p.latitud as number);
  const lngs = paradas.map((p) => p.longitud as number);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const dLat = maxLat - minLat || 1;
  const dLng = maxLng - minLng || 1;
  return paradas.map((p) => ({
    x: P + ((p.longitud as number) - minLng) / dLng * (W - 2 * P),
    y: P + (maxLat - (p.latitud as number)) / dLat * (H - 2 * P),
    parada: p,
  }));
}

// Diagrama de la ruta. Recibe: { paradas, alto? }.
export function DiagramaRuta({ paradas, alto = 220 }: Props) {
  const { colors } = useTheme();

  const conCoords = paradas
    .filter((p) => p.latitud != null && p.longitud != null)
    .slice()
    .sort((a, b) => a.secuencia - b.secuencia);

  if (conCoords.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Text style={{ color: colors.muted, textAlign: "center", fontSize: fontSize.body }}>
          Aún no hay paradas con ubicación para trazar la ruta.
        </Text>
      </View>
    );
  }

  const puntos = proyectar(conCoords, alto);
  const linea = puntos.map((pt) => `${pt.x},${pt.y}`).join(" ");
  // La "siguiente" parada = primera pendiente en orden de secuencia.
  const idxSiguiente = conCoords.findIndex((p) => p.estado_entrega === "PENDIENTE");

  const colorEstado = (estado: string) =>
    estado === "ENTREGADO" ? colors.success : estado === "FALLIDO" ? colors.danger : colors.warning;

  return (
    <View style={[estilos.caja, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <Svg width="100%" height={alto} viewBox={`0 0 ${W} ${alto}`}>
        {/* Línea del recorrido */}
        {puntos.length > 1 && (
          <Polyline points={linea} fill="none" stroke={colors.brand} strokeWidth={3} strokeLinejoin="round" />
        )}
        {/* Nodos de cada parada */}
        {puntos.map((pt, i) => {
          const esSiguiente = i === idxSiguiente;
          const r = esSiguiente ? 14 : 11;
          const fondo = esSiguiente ? colors.brand : colorEstado(pt.parada.estado_entrega);
          return (
            <Fragment key={pt.parada.pedido_id}>
              <Circle cx={pt.x} cy={pt.y} r={r} fill={fondo} stroke={colors.white} strokeWidth={2} />
              <SvgText x={pt.x} y={pt.y + 4} fontSize={11} fontWeight="bold" fill={colors.white} textAnchor="middle">
                {pt.parada.secuencia}
              </SvgText>
            </Fragment>
          );
        })}
      </Svg>
      <Text style={[estilos.leyenda, { color: colors.muted }]}>
        Ruta de referencia · 🔵 siguiente · 🟠 pendiente · 🟢 entregada · 🔴 fallida
      </Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.sm, paddingBottom: spacing.md },
  leyenda: { fontSize: fontSize.caption, textAlign: "center", marginTop: spacing.xs },
  vacio: { borderRadius: radius.lg, borderWidth: 1, alignItems: "center", justifyContent: "center", padding: 16 },
});
