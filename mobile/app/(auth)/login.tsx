// Pantalla de login del conductor (correo + contraseña). No hay registro: las
// cuentas se crean desde el panel admin.
import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Screen } from "@/components/Screen";
import { Field } from "@/components/Field";
import { Button } from "@/components/Button";
import { GradientHeader } from "@/components/GradientHeader";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
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
});
