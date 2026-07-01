// Pantalla de detalle de un reporte. Recibe el id por params y busca en la cache "mis-reportes".
import { ScrollView, StyleSheet, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Cabecera } from "@/components/Cabecera";
import { Card } from "@/components/Card";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { obtenerMisReportes } from "@/api/conductor";
import { claves } from "@/features/ruta/hooks";
import { useTheme, spacing, radius } from "@/theme";
import type { Reporte } from "@/types/api";

// Formatea una fecha ISO a "DD/MM/AAAA HH:MM" sin depender de Intl.
function fechaLegible(iso?: string | null): string {
  if (!iso) return "—";
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : iso;
}

export default function ReporteDetalleScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { colors } = useTheme();
  const reportes = useQuery({ queryKey: claves.misReportes, queryFn: obtenerMisReportes, refetchInterval: 10_000 });
  const r = reportes.data?.find((x: Reporte) => String(x.id) === String(id));

  if (reportes.isLoading && !r) {
    return <Screen conPadding={false}><Cabecera titulo="Reporte" atras /><Cargando /></Screen>;
  }
  if (!r) {
    return <Screen conPadding={false}><Cabecera titulo="Reporte" atras /><Vacio titulo="Reporte no encontrado" /></Screen>;
  }

  const resuelto = r.estado === "RESUELTO";

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Reporte" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <View style={estilos.filaTop}>
              <Texto variante="subtitle" color={colors.ink}>{r.pedido_codigo ?? `Pedido ${r.pedido_id}`}</Texto>
              <View style={[estilos.badge, { backgroundColor: resuelto ? colors.successSoft : colors.warningSoft }]}>
                <Texto variante="caption" color={resuelto ? colors.success : colors.warning}>{resuelto ? "Respondido" : "En revisión"}</Texto>
              </View>
            </View>
            <Dato etiqueta="Motivo" valor={r.motivo} c={colors} />
            {r.descripcion ? <Dato etiqueta="Descripción" valor={r.descripcion} c={colors} /> : null}
            {r.direccion_destino ? <Dato etiqueta="Dirección" valor={r.direccion_destino} c={colors} /> : null}
            <Dato etiqueta="Reportado" valor={fechaLegible(r.creado_en)} c={colors} />
          </Card>
        </Aparecer>

        <Aparecer delay={60}>
          <Card style={{ backgroundColor: resuelto ? colors.successSoft : colors.warningSoft }}>
            <Texto variante="subtitle" color={resuelto ? colors.success : colors.warning} style={{ marginBottom: spacing.xs }}>
              {resuelto ? "Respuesta de coordinación" : "En revisión"}
            </Texto>
            {resuelto ? (
              <>
                <Texto variante="body" color={colors.ink}>{r.respuesta || "Sin comentario."}</Texto>
                {r.accion ? <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.xs }}>Acción: {r.accion}</Texto> : null}
                <Texto variante="caption" color={colors.muted} style={{ marginTop: 2 }}>{fechaLegible(r.respondido_en)}</Texto>
              </>
            ) : (
              <Texto variante="body" color={colors.text}>Coordinación aún no responde tu reporte. Te avisaremos cuando haya respuesta.</Texto>
            )}
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor. Recibe: { etiqueta, valor, c (paleta) }.
function Dato({ etiqueta, valor, c }: { etiqueta: string; valor: string; c: { muted: string; ink: string } }) {
  return (
    <View style={estilos.dato}>
      <Texto variante="caption" color={c.muted}>{etiqueta}</Texto>
      <Texto variante="bodyMedium" color={c.ink}>{valor}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xl },
  filaTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.sm },
  badge: { borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  dato: { marginTop: spacing.md },
});
