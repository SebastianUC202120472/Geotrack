// Selector de mapa. Por defecto usa el mapa OSM (WebView, sin clave de Google) que
// funciona sin recompilar. Para usar el mapa NATIVO de Google, compila el APK con
// EXPO_PUBLIC_MAPA_NATIVO=1 (requiere también EXPO_PUBLIC_GOOGLE_MAPS_KEY en el build).
// Así el mismo código sirve para OSM (rápido) o Google (nativo) según la bandera.
import { MapaWeb } from "./MapaWeb";
import { MapaNativo } from "./MapaNativo";
import type { ParadaManifiesto } from "@/types/api";

// Usa el mapa nativo de Google SOLO si se pidió por bandera Y hay clave de Google
// en el build. Sin clave, react-native-maps crashea ("API key not found"), así
// que en ese caso caemos al mapa OSM (WebView), que no necesita clave.
const USAR_NATIVO =
  process.env.EXPO_PUBLIC_MAPA_NATIVO === "1" && !!process.env.EXPO_PUBLIC_GOOGLE_MAPS_KEY;

type Props = {
  paradas: ParadaManifiesto[];
  alto?: number;
};

// Mapa de la ruta. Recibe: { paradas, alto? }. Elige OSM o Google según la bandera de build.
export function Mapa({ paradas, alto = 260 }: Props) {
  return USAR_NATIVO ? <MapaNativo paradas={paradas} alto={alto} /> : <MapaWeb paradas={paradas} alto={alto} />;
}
