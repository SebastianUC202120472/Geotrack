// Pantalla de login del conductor (correo + contraseña). No hay registro: las
// cuentas se crean desde el panel admin.
import { useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Screen } from "@/components/Screen";
import { Field } from "@/components/Field";
import { Button } from "@/components/Button";
import { GradientHeader } from "@/components/GradientHeader";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
import { solicitarRestablecimiento } from "@/api/auth";
import { mensajeDeError } from "@/api/client";
import { useTheme, sombra, spacing, radius } from "@/theme";

// Formulario de inicio de sesión. Sin inputs (es la pantalla raíz de auth).
export default function LoginScreen() {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { iniciarSesion } = useAuth();
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  // Extra CUS-04: solicitud de restablecimiento de contraseña.
  const [mensajeSolicitud, setMensajeSolicitud] = useState("");
  const [solicitando, setSolicitando] = useState(false);

  // Valida y ejecuta el inicio de sesión. Sin parámetros (usa el estado local).
  const entrar = async () => {
    if (!correo.trim() || !contrasena) {
      setError("Ingresa tu correo y contraseña.");
      return;
    }
    setError("");
    setCargando(true);
    try {
      await iniciarSesion(correo.trim(), contrasena);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  };

  // Pide al admin que restablezca la clave (usa el correo escrito arriba). El backend
  // responde un mensaje genérico exista o no la cuenta.
  const solicitarReset = async () => {
    if (!correo.trim()) {
      setError("Escribe tu correo arriba y vuelve a tocar para solicitar el restablecimiento.");
      return;
    }
    setError("");
    setMensajeSolicitud("");
    setSolicitando(true);
    try {
      const r = await solicitarRestablecimiento(correo.trim());
      setMensajeSolicitud(r.mensaje);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setSolicitando(false);
    }
  };

  return (
    <Screen conPadding={false}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={estilos.contenedor}>
        {/* Hero a sangre completa: el degradado sube bajo la barra de estado (sin hueco). */}
        <GradientHeader style={[estilos.cabecera, { paddingTop: insets.top + spacing.xxl }]}>
          <View style={estilos.marca}>
            <View style={[estilos.logo, sombra(colors), { backgroundColor: colors.overlay }]}>
              <Texto variante="display" color={colors.white}>G</Texto>
            </View>
            <Texto variante="title" color={colors.white}>GeoTrack</Texto>
            <Texto variante="body" color={colors.white} style={estilos.subtitulo}>App del conductor</Texto>
          </View>
        </GradientHeader>

        {/* Tarjeta del formulario superpuesta al hero (da profundidad). */}
        <Aparecer style={estilos.cuerpo}>
          <View style={[estilos.tarjeta, sombra(colors), { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Field label="Correo" value={correo} onChangeText={setCorreo} placeholder="conductor@siol.com"
              icono="mail-outline" keyboardType="email-address" autoCapitalize="none" autoComplete="email" />
            <Field label="Contraseña" value={contrasena} onChangeText={setContrasena} placeholder="••••••••"
              icono="lock-closed-outline" secureTextEntry autoComplete="password" />

            {error ? (
              <Texto variante="body" color={colors.danger} style={[estilos.error, { backgroundColor: colors.dangerSoft }]}>{error}</Texto>
            ) : null}

            <Button titulo={cargando ? "Ingresando…" : "Iniciar sesión"} onPress={entrar} cargando={cargando} />

            {/* Extra CUS-04: solicitar restablecimiento de contraseña */}
            <Pressable onPress={solicitarReset} disabled={solicitando} accessibilityRole="button"
              accessibilityLabel="Olvidé mi contraseña" style={estilos.olvide}>
              <Texto variante="body" color={colors.brand}>
                {solicitando ? "Enviando solicitud…" : "¿Olvidaste tu contraseña?"}
              </Texto>
            </Pressable>
            {mensajeSolicitud ? (
              <Texto variante="caption" color={colors.text} style={[estilos.info, { backgroundColor: colors.brandSoft }]}>
                {mensajeSolicitud}
              </Texto>
            ) : null}
          </View>
        </Aparecer>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1 },
  // Hero alto, con espacio extra abajo para que la tarjeta se superponga.
  cabecera: { paddingBottom: spacing.xxl + spacing.xl },
  marca: { alignItems: "center", gap: spacing.sm },
  logo: { width: 76, height: 76, borderRadius: radius.xl, alignItems: "center", justifyContent: "center" },
  subtitulo: { textAlign: "center", opacity: 0.9 },
  // La tarjeta sube sobre el hero (margen negativo) para dar profundidad.
  cuerpo: { paddingHorizontal: spacing.lg, marginTop: -spacing.xl },
  tarjeta: { borderRadius: radius.xl, borderWidth: 1, padding: spacing.lg, gap: spacing.lg },
  error: { padding: spacing.md, borderRadius: radius.md, textAlign: "center" },
  olvide: { alignItems: "center", paddingVertical: spacing.xs },
  info: { padding: spacing.md, borderRadius: radius.md, textAlign: "center" },
});
