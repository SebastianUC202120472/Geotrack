// Perfil del conductor: SUS DATOS PERSONALES (foto, nombre, correo, código, DNI,
// teléfono, vehículo). Los reportes están en su propia pestaña (reportes.tsx) y
// los ajustes en la suya (ajustes.tsx). Se abre desde la foto de la cabecera.
import { ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { Cargando } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { obtenerPerfil } from "@/api/conductor";
import { useTheme, spacing, radius } from "@/theme";
import { colorDeNombre } from "@/utils/colorDeNombre";
import { urlMedia } from "@/api/config";

export default function PerfilScreen() {
  const { colors } = useTheme();
  const perfil = useQuery({ queryKey: ["perfil"], queryFn: obtenerPerfil, refetchInterval: 10_000, refetchOnMount: "always" });

  if (perfil.isLoading) return <Screen conPadding={false}><Cabecera titulo="Mi perfil" atras /><Cargando /></Screen>;

  const p = perfil.data;
  const inicial = (p?.nombre || p?.correo || "?").charAt(0).toUpperCase();
  const fotoUri = urlMedia(p?.foto_url);

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Mi perfil" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        {/* Identidad: foto grande + nombre + código */}
        <Aparecer>
          <View style={estilos.identidad}>
            {fotoUri ? (
              <Image source={{ uri: fotoUri }} style={estilos.fotoGrande} contentFit="cover" transition={250} />
            ) : (
              <View style={[estilos.fotoGrande, estilos.fallback, { backgroundColor: colorDeNombre(p?.nombre) }]}>
                <Texto variante="display" color={colors.white}>{inicial}</Texto>
              </View>
            )}
            <Texto variante="title" color={colors.ink} style={{ marginTop: spacing.md }} numberOfLines={1}>{p?.nombre || "Conductor"}</Texto>
            <Texto variante="caption" color={colors.muted}>{p?.codigo || "—"}</Texto>
          </View>
        </Aparecer>

        {/* Datos personales */}
        <Aparecer delay={60}>
          <Card>
            <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Datos personales</Texto>
            <Dato icono="mail-outline" etiqueta="Correo" valor={p?.correo || "—"} c={colors} />
            <Dato icono="card-outline" etiqueta="DNI" valor={p?.dni || "—"} c={colors} />
            <Dato icono="call-outline" etiqueta="Teléfono" valor={p?.telefono || "—"} c={colors} />
            <Dato icono="car-outline" etiqueta="Vehículo" valor={p?.vehiculo ? p.vehiculo.placa : "Sin asignar"} c={colors} />
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor con icono. Recibe: { icono, etiqueta, valor, c (paleta) }.
function Dato({ icono, etiqueta, valor, c }: { icono: keyof typeof Ionicons.glyphMap; etiqueta: string; valor: string; c: { muted: string; ink: string; brandSoft: string; brand: string } }) {
  return (
    <View style={estilos.dato}>
      <View style={[estilos.datoIcono, { backgroundColor: c.brandSoft }]}>
        <Ionicons name={icono} size={18} color={c.brand} />
      </View>
      <View style={{ flex: 1 }}>
        <Texto variante="caption" color={c.muted}>{etiqueta}</Texto>
        <Texto variante="bodyMedium" color={c.ink}>{valor}</Texto>
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xl },
  identidad: { alignItems: "center" },
  fotoGrande: { width: 96, height: 96, borderRadius: radius.pill, borderWidth: 3, borderColor: "#FFFFFF" },
  fallback: { alignItems: "center", justifyContent: "center" },
  titulo: { marginBottom: spacing.md },
  dato: { flexDirection: "row", alignItems: "center", gap: spacing.md, marginBottom: spacing.md },
  datoIcono: { width: 40, height: 40, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
});
