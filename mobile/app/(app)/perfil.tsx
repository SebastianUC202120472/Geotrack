// Perfil del conductor: sus datos, ajustes de tema (claro/oscuro + color),
// contacto con coordinación, sus reportes y cierre de sesión.
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cargando } from "@/components/Estados";
import { useAuth } from "@/store/auth";
import { obtenerPerfil, obtenerMisReportes } from "@/api/conductor";
import { useTheme, spacing, fontSize, radius, ACENTOS, type Modo, type Acento } from "@/theme";
import type { Reporte } from "@/types/api";

// Número de coordinación para llamar/escribir. Cámbialo por el real (o usa env).
const TELEFONO_COORDINACION = process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "+51999888777";
const MODOS: { valor: Modo; etiqueta: string }[] = [
  { valor: "system", etiqueta: "Sistema" },
  { valor: "light", etiqueta: "Claro" },
  { valor: "dark", etiqueta: "Oscuro" },
];

export default function PerfilScreen() {
  const { colors, modo, setModo, acento, setAcento } = useTheme();
  const { cerrarSesion } = useAuth();
  const perfil = useQuery({ queryKey: ["perfil"], queryFn: obtenerPerfil });
  const reportes = useQuery({ queryKey: ["mis-reportes"], queryFn: obtenerMisReportes });

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
        <Card>
          <View style={estilos.cabecera}>
            <View style={[estilos.avatar, { backgroundColor: colors.brand }]}>
              <Text style={[estilos.avatarTexto, { color: colors.white }]}>{inicial}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[estilos.nombre, { color: colors.ink }]}>{p?.nombre || "Conductor"}</Text>
              <Text style={[estilos.dato, { color: colors.muted }]}>{p?.codigo} · {p?.correo}</Text>
              {p?.vehiculo && (
                <Text style={[estilos.dato, { color: colors.muted }]}>Vehículo: {p.vehiculo.placa}</Text>
              )}
            </View>
          </View>
        </Card>

        {/* Ajustes de tema */}
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
                  <Text style={{ color: activo ? colors.brand : colors.text, fontWeight: "700" }}>{m.etiqueta}</Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={[estilos.sub, { color: colors.muted, marginTop: spacing.md }]}>Color de acento</Text>
          <View style={estilos.fila}>
            {ACENTOS.map((a) => (
              <Pressable
                key={a}
                onPress={() => setAcento(a)}
                accessibilityRole="button"
                accessibilityLabel={`Color ${a}`}
                style={[estilos.colorChip, { borderColor: acento === a ? colors.ink : colors.border }]}
              >
                <View style={[estilos.colorPunto, { backgroundColor: COLOR_ACENTO[a] }]} />
                <Text style={{ color: colors.text, textTransform: "capitalize" }}>{a}</Text>
              </Pressable>
            ))}
          </View>
        </Card>

        {/* Contacto con coordinación */}
        <Card>
          <Text style={[estilos.titulo, { color: colors.ink }]}>¿Algún problema?</Text>
          <Text style={[estilos.sub, { color: colors.muted }]}>Contacta a coordinación o repórtalo desde el pedido.</Text>
          <View style={[estilos.fila, { marginTop: spacing.md }]}>
            <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
            <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
          </View>
        </Card>

        {/* Mis reportes */}
        <Card>
          <Text style={[estilos.titulo, { color: colors.ink }]}>Mis reportes</Text>
          {(reportes.data?.length ?? 0) === 0 ? (
            <Text style={[estilos.sub, { color: colors.muted }]}>No has enviado reportes.</Text>
          ) : (
            reportes.data!.map((r: Reporte) => (
              <View key={r.id} style={[estilos.reporte, { borderColor: colors.border }]}>
                <Text style={{ color: colors.ink, fontWeight: "700" }}>{r.pedido_codigo} · {r.motivo}</Text>
                <Text style={{ color: r.estado === "RESUELTO" ? colors.success : colors.warning, fontWeight: "700", fontSize: fontSize.caption }}>
                  {r.estado === "RESUELTO" ? "Respondido" : "En revisión"}
                </Text>
                {r.respuesta ? <Text style={{ color: colors.text, marginTop: 2 }}>{r.respuesta}</Text> : null}
              </View>
            ))
          )}
        </Card>

        <Button titulo="Cerrar sesión" variante="danger" onPress={cerrarSesion} />
      </ScrollView>
    </Screen>
  );
}

// Color de muestra de cada acento (solo para los botones de selección).
const COLOR_ACENTO: Record<Acento, string> = { azul: "#2563EB", verde: "#16A34A", naranja: "#EA580C" };

const estilos = StyleSheet.create({
  contenido: { padding: spacing.lg, gap: spacing.lg },
  cabecera: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
  avatar: { width: 56, height: 56, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  avatarTexto: { fontSize: fontSize.title, fontWeight: "800" },
  nombre: { fontSize: fontSize.title, fontWeight: "800" },
  dato: { fontSize: fontSize.caption, marginTop: 2 },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700", marginBottom: spacing.sm },
  sub: { fontSize: fontSize.caption },
  fila: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  chip: { flex: 1, alignItems: "center", paddingVertical: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  colorChip: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  colorPunto: { width: 18, height: 18, borderRadius: radius.pill },
  reporte: { borderTopWidth: 1, paddingTop: spacing.sm, marginTop: spacing.sm },
});
