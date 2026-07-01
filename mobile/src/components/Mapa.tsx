import { MapaWeb } from "./MapaWeb";
import { MapaNativo } from "./MapaNativo";
import type { ParadaManifiesto } from "@/types/api";

// Usa mapa nativo (Google) si hay clave de build; si no, cae a OSM (WebView).
const USAR_NATIVO = !!process.env.EXPO_PUBLIC_GOOGLE_MAPS_KEY;

type Props = {
  paradas: ParadaManifiesto[];
  alto?: number;
};

// Mapa de la ruta. Recibe: { paradas, alto? }. Elige OSM o Google según la bandera de build.
export function Mapa({ paradas, alto = 260 }: Props) {
  return USAR_NATIVO ? <MapaNativo paradas={paradas} alto={alto} /> : <MapaWeb paradas={paradas} alto={alto} />;
}
