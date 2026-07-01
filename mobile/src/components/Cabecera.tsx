// Cabecera superior con título, campana y avatar del conductor. Recibe: { titulo, atras? }.
import { Pressable, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Texto } from "@/components/Texto";
import { useTheme, spacing, radius } from "@/theme";
import { obtenerPerfil } from "@/api/conductor";
import { colorDeNombre } from "@/utils/colorDeNombre";
import { urlMedia } from "@/api/config";

export function Cabecera({ titulo, atras }: { titulo: string; atras?: boolean }) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { data: p } = useQuery({ queryKey: ["perfil"], queryFn: obtenerPerfil, refetchInterval: 10_000 });
  const fotoUri = urlMedia(p?.foto_url);
  const inicial = (p?.nombre || p?.correo || "?").charAt(0).toUpperCase();

  const padTop = { paddingTop: insets.top + spacing.sm };

  if (atras) {
    return (
      <View style={[estilos.cont, padTop, { backgroundColor: colors.canvas, borderBottomColor: colors.border }]}>
        <Pressable
          onPress={() => router.back()}
          hitSlop={10}
          accessibilityRole="button"
          accessibilityLabel="Atrás"
          style={[estilos.iconoBtn, { backgroundColor: colors.surface, borderColor: colors.border }]}
        >
          <Ionicons name="arrow-back" size={22} color={colors.ink} />
        </Pressable>
        <Texto variante="title" color={colors.ink} style={estilos.titulo} numberOfLines={1}>{titulo}</Texto>
      </View>
    );
  }

  return (
    <View style={[estilos.cont, padTop, { backgroundColor: colors.canvas, borderBottomColor: colors.border }]}>
      <Texto variante="title" color={colors.ink} style={estilos.titulo} numberOfLines={1}>{titulo}</Texto>

      <Pressable
        onPress={() => router.push("/notificaciones")}
        hitSlop={10}
        accessibilityRole="button"
        accessibilityLabel="Notificaciones"
        style={[estilos.iconoBtn, { backgroundColor: colors.surface, borderColor: colors.border }]}
      >
        <Ionicons name="notifications-outline" size={20} color={colors.text} />
      </Pressable>

      <Pressable onPress={() => router.push("/perfil")} hitSlop={10} accessibilityRole="button" accessibilityLabel="Mi perfil">
        {fotoUri ? (
          <Image source={{ uri: fotoUri }} style={estilos.avatar} contentFit="cover" transition={200} />
        ) : (
          <View style={[estilos.avatar, estilos.avatarFallback, { backgroundColor: colorDeNombre(p?.nombre) }]}>
            <Texto variante="label" color={colors.white}>{inicial}</Texto>
          </View>
        )}
      </Pressable>
    </View>
  );
}

const estilos = StyleSheet.create({
  cont: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingHorizontal: spacing.lg, paddingBottom: spacing.sm, borderBottomWidth: 1 },
  titulo: { flex: 1 },
  iconoBtn: { width: 38, height: 38, borderRadius: radius.pill, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  avatar: { width: 38, height: 38, borderRadius: radius.pill },
  avatarFallback: { alignItems: "center", justifyContent: "center" },
});
