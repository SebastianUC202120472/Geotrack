// Perfil del conductor: sus datos, ajuste de tema (claro/oscuro), contacto con
// coordinación, sus reportes y cierre de sesión.
import { Linking, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cargando } from "@/components/Estados";
import { Aparecer, Contador } from "@/components/Animations";
import { GradientHeader } from "@/components/GradientHeader";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
import { obtenerPerfil, obtenerMisReportes } from "@/api/conductor";
import { useTheme, spacing, radius, type Modo } from "@/theme";
import { colorDeNombre } from "@/utils/colorDeNombre";
import { urlMedia } from "@/api/config";
import type { Reporte } from "@/types/api";

// Número de coordinación para llamar/escribir. Cámbialo por el real (o usa env).
const TELEFONO_COORDINACION = process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "+51999888777";
const MODOS: { valor: Modo; etiqueta: string; icono: keyof typeof Ionicons.glyphMap }[] = [
  { valor: "system", etiqueta: "Sistema", icono: "phone-portrait-outline" },
  { valor: "light", etiqueta: "Claro", icono: "sunny-outline" },
  { valor: "dark", etiqueta: "Oscuro", icono: "moon-outline" },
];

export default function PerfilScreen() {
  const { colors, modo, setModo } = useTheme();
  const { cerrarSesion } = useAuth();
  const perfil = useQuery({
    queryKey: ["perfil"],
    queryFn: obtenerPerfil,
    refetchInterval: 10_000,
    refetchOnMount: "always",
  });
  const reportes = useQuery({
    queryKey: ["mis-reportes"],
    queryFn: obtenerMisReportes,
    refetchInterval: 10_000,
    refetchOnMount: "always",
  });

  // Abre el marcador con el número de coordinación.
  const llamar = () => Linking.openURL(`tel:${TELEFONO_COORDINACION.replace(/\s/g, "")}`);
  // Abre WhatsApp con el número de coordinación.
  const whatsapp = () =>
    Linking.openURL(`https://wa.me/${TELEFONO_COORDINACION.replace(/[^\d]/g, "")}`);

  if (perfil.isLoading) return <Screen><Cargando /></Screen>;

  const p = perfil.data;
  const inicial = (p?.nombre || p?.correo || "?").charAt(0).toUpperCase();

  // Conteo de reportes para los mini-stats del header.
  const totalReportes = reportes.data?.length ?? 0;
  const respondidos = (reportes.data ?? []).filter((r: Reporte) => r.estado === "RESUELTO").length;
  // URI de la foto del conductor subida por el admin; undefined si no tiene.
  const fotoUri = urlMedia(p?.foto_url);

  return (
    <Screen conPadding={false}>
      <ScrollView contentContainerStyle={estilos.contenido}>
        {/* Identidad: foto/inicial, datos, vehículo y mini-stats de reportes */}
        <GradientHeader>
          <View style={estilos.cabecera}>
            {fotoUri ? (
              // Foto real del conductor cargada con transición suave.
              <Image
                source={{ uri: fotoUri }}
                style={estilos.avatarFoto}
                contentFit="cover"
                transition={250}
              />
            ) : (
              // Fallback: inicial con color determinista por nombre.
              <View style={[estilos.avatar, { backgroundColor: colorDeNombre(p?.nombre) }]}>
                <Texto variante="title" color={colors.white}>{inicial}</Texto>
              </View>
            )}
            <View style={{ flex: 1 }}>
              <Texto variante="title" color={colors.white} numberOfLines={1}>
                {p?.nombre || "Conductor"}
              </Texto>
              <Texto variante="caption" color={colors.white} style={{ opacity: 0.9 }} numberOfLines={1}>
                {p?.codigo} · {p?.correo}
              </Texto>
              {p?.vehiculo && (
                <View style={[estilos.vehiculo, { backgroundColor: colors.overlay }]}>
                  <Ionicons name="car-outline" size={14} color={colors.white} />
                  <Texto variante="caption" color={colors.white}>{p.vehiculo.placa}</Texto>
                </View>
              )}
            </View>
          </View>

          {/* Mini-stats: total de reportes y cuántos están respondidos */}
          <View style={estilos.stats}>
            <View style={[estilos.stat, { backgroundColor: colors.overlay }]}>
              <Contador valor={totalReportes} variante="subtitle" color={colors.white} />
              <Texto variante="caption" color={colors.white} style={{ opacity: 0.9 }}>Reportes</Texto>
            </View>
            <View style={[estilos.stat, { backgroundColor: colors.overlay }]}>
              <Contador valor={respondidos} variante="subtitle" color={colors.white} />
              <Texto variante="caption" color={colors.white} style={{ opacity: 0.9 }}>Respondidos</Texto>
            </View>
          </View>
        </GradientHeader>

        <View style={estilos.cuerpo}>
          {/* Ajuste de tema */}
          <Aparecer delay={0}>
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Apariencia</Texto>
              <Texto variante="caption" color={colors.muted} style={estilos.sub}>Tema</Texto>
              <View style={estilos.fila}>
                {MODOS.map((m) => {
                  const activo = modo === m.valor;
                  return (
                    <Pressable
                      key={m.valor}
                      onPress={() => setModo(m.valor)}
                      accessibilityRole="button"
                      accessibilityLabel={`Tema ${m.etiqueta}`}
                      style={({ pressed }) => [
                        estilos.chip,
                        { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface },
                        pressed && { opacity: 0.85 },
                      ]}
                    >
                      <Ionicons name={m.icono} size={20} color={activo ? colors.brand : colors.text} />
                      <Texto variante="label" color={activo ? colors.brand : colors.text}>{m.etiqueta}</Texto>
                    </Pressable>
                  );
                })}
              </View>
            </Card>
          </Aparecer>

          {/* Contacto con coordinación */}
          <Aparecer delay={60}>
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>¿Algún problema?</Texto>
              <Texto variante="caption" color={colors.muted} style={estilos.sub}>
                Contacta a coordinación o repórtalo desde el pedido.
              </Texto>
              <View style={[estilos.fila, { marginTop: spacing.md }]}>
                <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
                <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
              </View>
            </Card>
          </Aparecer>

          {/* Mis reportes */}
          <Aparecer delay={120}>
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Mis reportes</Texto>
              {(reportes.data?.length ?? 0) === 0 ? (
                <Texto variante="caption" color={colors.muted} style={estilos.sub}>No has enviado reportes.</Texto>
              ) : (
                reportes.data!.map((r: Reporte) => {
                  const resuelto = r.estado === "RESUELTO";
                  return (
                    <View key={r.id} style={[estilos.reporte, { borderColor: colors.border }]}>
                      <Texto variante="bodyMedium" color={colors.ink}>{r.pedido_codigo} · {r.motivo}</Texto>
                      <View
                        style={[
                          estilos.badge,
                          { backgroundColor: resuelto ? colors.successSoft : colors.warningSoft },
                        ]}
                      >
                        <Texto variante="caption" color={resuelto ? colors.success : colors.warning}>
                          {resuelto ? "Respondido" : "En revisión"}
                        </Texto>
                      </View>
                      {r.respuesta ? (
                        <Texto variante="body" color={colors.text} style={{ marginTop: 2 }}>
                          {r.respuesta}
                        </Texto>
                      ) : null}
                    </View>
                  );
                })
              )}
            </Card>
          </Aparecer>

          <Aparecer delay={180}>
            <Button titulo="Cerrar sesión" variante="danger" onPress={cerrarSesion} />
          </Aparecer>
        </View>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  contenido: { paddingBottom: spacing.xl },
  cuerpo: { padding: spacing.lg, gap: spacing.lg },
  cabecera: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
  // Avatar de inicial: borde blanco + color de fondo determinista.
  avatar: { width: 66, height: 66, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", borderWidth: 3, borderColor: "#FFFFFF" },
  // Avatar de foto real: mismas dimensiones y borde blanco.
  avatarFoto: { width: 66, height: 66, borderRadius: radius.pill, borderWidth: 3, borderColor: "#FFFFFF" },
  // Chip de vehículo en el header.
  vehiculo: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs, alignSelf: "flex-start", paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: radius.pill },
  // Fila de mini-stats bajo los datos del conductor.
  stats: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.lg },
  stat: { flex: 1, borderRadius: radius.md, padding: spacing.md, gap: 2 },
  titulo: { marginBottom: spacing.sm },
  sub: {},
  fila: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  chip: { flex: 1, alignItems: "center", gap: spacing.xs, paddingVertical: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  reporte: { borderTopWidth: 1, paddingTop: spacing.sm, marginTop: spacing.sm },
  badge: { alignSelf: "flex-start", borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, marginTop: spacing.xs },
});
