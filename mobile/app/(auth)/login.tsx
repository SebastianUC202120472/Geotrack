// Pantalla de login del conductor. Recibe: nada (accede al estado global de auth).
import { useState } from "react";
import { Image } from "expo-image";
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

export default function LoginScreen() {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const { iniciarSesion } = useAuth();
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mensajeSolicitud, setMensajeSolicitud] = useState("");
  const [solicitando, setSolicitando] = useState(false);

  // Valida y llama a iniciarSesion con correo y contrasena del estado local.
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

  // Solicita restablecimiento de contrasena al backend usando el correo del estado.
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
        <GradientHeader style={[estilos.cabecera, { paddingTop: insets.top + spacing.xxl }]}>
          <View style={estilos.marca}>
            <Image source={require("../../assets/logo.png")} style={estilos.logo} contentFit="contain" />
            <Texto variante="title" color={colors.white}>GeoTrack</Texto>
            <Texto variante="body" color={colors.white} style={estilos.subtitulo}>App del conductor</Texto>
          </View>
        </GradientHeader>

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
  cabecera: { paddingBottom: spacing.xxl + spacing.xl },
  marca: { alignItems: "center", gap: spacing.sm },
  logo: { width: 76, height: 76, borderRadius: radius.xl, alignItems: "center", justifyContent: "center" },
  subtitulo: { textAlign: "center", opacity: 0.9 },
  cuerpo: { paddingHorizontal: spacing.lg, marginTop: -spacing.xl },
  tarjeta: { borderRadius: radius.xl, borderWidth: 1, padding: spacing.lg, gap: spacing.lg },
  error: { padding: spacing.md, borderRadius: radius.md, textAlign: "center" },
  olvide: { alignItems: "center", paddingVertical: spacing.xs },
  info: { padding: spacing.md, borderRadius: radius.md, textAlign: "center" },
});
