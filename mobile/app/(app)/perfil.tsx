// Perfil del conductor: sus datos, ajuste de tema (claro/oscuro), contacto con
// coordinación, sus reportes y cierre de sesión.
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cargando } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { GradientHeader } from "@/components/GradientHeader";
import { useAuth } from "@/store/auth";
import { obtenerPerfil, obtenerMisReportes } from "@/api/conductor";
import { useTheme, spacing, fontSize, radius, type Modo } from "@/theme";
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

  return (
    <Screen conPadding={false}>
      <ScrollView contentContainerStyle={estilos.contenido}>
        {/* Identidad */}
        <GradientHeader>
          <View style={estilos.cabecera}>
            <View style={[estilos.avatar, { backgroundColor: colors.white }]}>
              <Text style={[estilos.avatarTexto, { color: colors.brand }]}>{inicial}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[estilos.nombre, { color: colors.white }]}>{p?.nombre || "Conductor"}</Text>
              <Text style={[estilos.dato, { color: colors.white }]}>{p?.codigo} · {p?.correo}</Text>
              {p?.vehiculo && (
                <View style={estilos.vehiculo}>
                  <Ionicons name="car-outline" size={14} color={colors.white} />
                  <Text style={[estilos.dato, { color: colors.white }]}>{p.vehiculo.placa}</Text>
                </View>
              )}
            </View>
          </View>
        </GradientHeader>

        <View style={estilos.cuerpo}>
          {/* Ajuste de tema */}
          <Aparecer delay={0}>
            <Card>
              <Text style={[estilos.titulo, { color: colors.ink }]}>Apariencia</Text>
              <Text style={[estilos.sub, { color: colors.muted }]}>Tema</Text>
              <View style={estilos.fila}>
                {MODOS.map((m) => {
                  const activo = modo === m.valor;
                  return (
                    <Pressable
                      key={m.valor}
                      onPress={() => setModo(m.valor)}
                      accessibilityRole="button"
                      accessibilityLabel={`Tema ${m.etiqueta}`}
                      style={[
                        estilos.chip,
                        { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface },
                      ]}
                    >
                      <Ionicons name={m.icono} size={20} color={activo ? colors.brand : colors.text} />
                      <Text style={{ color: activo ? colors.brand : colors.text, fontWeight: "700" }}>{m.etiqueta}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </Card>
          </Aparecer>

          {/* Contacto con coordinación */}
          <Aparecer delay={60}>
            <Card>
              <Text style={[estilos.titulo, { color: colors.ink }]}>¿Algún problema?</Text>
              <Text style={[estilos.sub, { color: colors.muted }]}>Contacta a coordinación o repórtalo desde el pedido.</Text>
              <View style={[estilos.fila, { marginTop: spacing.md }]}>
                <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
                <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
              </View>
            </Card>
          </Aparecer>

          {/* Mis reportes */}
          <Aparecer delay={120}>
            <Card>
              <Text style={[estilos.titulo, { color: colors.ink }]}>Mis reportes</Text>
              {(reportes.data?.length ?? 0) === 0 ? (
                <Text style={[estilos.sub, { color: colors.muted }]}>No has enviado reportes.</Text>
              ) : (
                reportes.data!.map((r: Reporte) => {
                  const resuelto = r.estado === "RESUELTO";
                  return (
                    <View key={r.id} style={[estilos.reporte, { borderColor: colors.border }]}>
                      <Text style={{ color: colors.ink, fontWeight: "700" }}>{r.pedido_codigo} · {r.motivo}</Text>
                      <View
                        style={[
                          estilos.badge,
                          { backgroundColor: resuelto ? colors.successSoft : colors.warningSoft },
                        ]}
                      >
                        <Text style={{ color: resuelto ? colors.success : colors.warning, fontWeight: "700", fontSize: fontSize.caption }}>
                          {resuelto ? "Respondido" : "En revisión"}
                        </Text>
                      </View>
                      {r.respuesta ? <Text style={{ color: colors.text, marginTop: 2 }}>{r.respuesta}</Text> : null}
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
  avatar: { width: 56, height: 56, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  avatarTexto: { fontSize: fontSize.title, fontWeight: "800" },
  nombre: { fontSize: fontSize.title, fontWeight: "800" },
  dato: { fontSize: fontSize.caption, marginTop: 2 },
  vehiculo: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: 2 },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700", marginBottom: spacing.sm },
  sub: { fontSize: fontSize.caption },
  fila: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  chip: { flex: 1, alignItems: "center", gap: spacing.xs, paddingVertical: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  reporte: { borderTopWidth: 1, paddingTop: spacing.sm, marginTop: spacing.sm },
  badge: { alignSelf: "flex-start", borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, marginTop: spacing.xs },
});
