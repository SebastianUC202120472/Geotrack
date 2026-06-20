// Perfil del conductor: SUS DATOS PERSONALES (foto, nombre, correo, código, DNI,
// teléfono, vehículo) y sus reportes. Los ajustes viven en su propio apartado
// (ajustes.tsx). Pantalla navegable desde la foto de la cabecera (con back).
import { ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { CamionCargando } from "@/components/CamionCargando";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { obtenerPerfil, obtenerMisReportes } from "@/api/conductor";
import { useTheme, spacing, radius } from "@/theme";
import { colorDeNombre } from "@/utils/colorDeNombre";
import { urlMedia } from "@/api/config";
import type { Reporte } from "@/types/api";

export default function PerfilScreen() {
  const { colors } = useTheme();
  const perfil = useQuery({ queryKey: ["perfil"], queryFn: obtenerPerfil, refetchInterval: 10_000, refetchOnMount: "always" });
  const reportes = useQuery({ queryKey: ["mis-reportes"], queryFn: obtenerMisReportes, refetchInterval: 10_000, refetchOnMount: "always" });

  if (perfil.isLoading) return <Screen><CamionCargando texto="Cargando tu perfil…" /></Screen>;

  const p = perfil.data;
  const inicial = (p?.nombre || p?.correo || "?").charAt(0).toUpperCase();
  const fotoUri = urlMedia(p?.foto_url);

  return (
    <Screen conPadding={false}>
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

        {/* Mis reportes */}
        <Aparecer delay={120}>
          <Card>
            <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Mis reportes</Texto>
            {(reportes.data?.length ?? 0) === 0 ? (
              <Texto variante="caption" color={colors.muted}>No has enviado reportes.</Texto>
            ) : (
              reportes.data!.map((r: Reporte) => {
                const resuelto = r.estado === "RESUELTO";
                return (
                  <View key={r.id} style={[estilos.reporte, { borderColor: colors.border }]}>
                    <Texto variante="bodyMedium" color={colors.ink}>{r.pedido_codigo} · {r.motivo}</Texto>
                    <View style={[estilos.badge, { backgroundColor: resuelto ? colors.successSoft : colors.warningSoft }]}>
                      <Texto variante="caption" color={resuelto ? colors.success : colors.warning}>{resuelto ? "Respondido" : "En revisión"}</Texto>
                    </View>
                    {r.respuesta ? <Texto variante="body" color={colors.text} style={{ marginTop: 2 }}>{r.respuesta}</Texto> : null}
                  </View>
                );
              })
            )}
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
  reporte: { borderTopWidth: 1, paddingTop: spacing.sm, marginTop: spacing.sm },
  badge: { alignSelf: "flex-start", borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, marginTop: spacing.xs },
});
