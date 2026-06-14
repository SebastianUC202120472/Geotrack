// Pantalla de login del conductor (correo + contraseña). No hay registro: las
// cuentas se crean desde el panel admin.
import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";
import { Screen } from "@/components/Screen";
import { Field } from "@/components/Field";
import { Button } from "@/components/Button";
import { GradientHeader } from "@/components/GradientHeader";
import { Aparecer } from "@/components/Animations";
import { useAuth } from "@/store/auth";
import { mensajeDeError } from "@/api/client";
import { useTheme, fontSize, spacing, radius } from "@/theme";

// Formulario de inicio de sesión. Sin inputs (es la pantalla raíz de auth).
export default function LoginScreen() {
  const { colors } = useTheme();
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
        <GradientHeader style={estilos.cabecera}>
          <View style={estilos.marca}>
            <View style={[estilos.logo, { backgroundColor: "rgba(255,255,255,0.18)" }]}>
              <Text style={[estilos.logoTexto, { color: colors.white }]}>G</Text>
            </View>
            <Text style={[estilos.titulo, { color: colors.white }]}>GeoTrack</Text>
            <Text style={[estilos.subtitulo, { color: colors.white }]}>App del conductor</Text>
          </View>
        </GradientHeader>

        <Aparecer style={estilos.cuerpo}>
          <View style={[estilos.tarjeta, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Field label="Correo" value={correo} onChangeText={setCorreo} placeholder="conductor@siol.com"
              icono="mail-outline" keyboardType="email-address" autoCapitalize="none" autoComplete="email" />
            <Field label="Contraseña" value={contrasena} onChangeText={setContrasena} placeholder="••••••••"
              icono="lock-closed-outline" secureTextEntry autoComplete="password" />

            {error ? (
              <Text style={[estilos.error, { backgroundColor: colors.dangerSoft, color: colors.danger }]}>{error}</Text>
            ) : null}

            <Button titulo={cargando ? "Ingresando…" : "Iniciar sesión"} onPress={entrar} cargando={cargando} />
          </View>
        </Aparecer>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  contenedor: { flex: 1, justifyContent: "center", gap: spacing.xl },
  cabecera: { paddingVertical: spacing.xxl },
  marca: { alignItems: "center", gap: spacing.sm },
  logo: { width: 64, height: 64, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  logoTexto: { fontSize: fontSize.display, fontWeight: "800" },
  titulo: { fontSize: fontSize.title, fontWeight: "800" },
  subtitulo: { fontSize: fontSize.body, textAlign: "center", opacity: 0.9 },
  cuerpo: { paddingHorizontal: spacing.lg },
  tarjeta: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg, gap: spacing.lg, shadowColor: "#0F172A", shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 2 },
  error: { padding: spacing.md, borderRadius: radius.md, fontSize: fontSize.body, textAlign: "center" },
});
