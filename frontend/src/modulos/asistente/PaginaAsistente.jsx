// Vista completa "Asistente IA" del menu lateral. Reutiliza el mismo chat del widget
// (y la misma conversacion), con graficos mas grandes y enlaces a la pantalla de origen.
import PageHeader from "../../components/ui/PageHeader";
import EmptyState from "../../components/ui/EmptyState";
import { useAuth } from "../../hooks/useAuth";
import ChatAsistente from "./ChatAsistente";
import IconoAsistente from "./IconoAsistente";
import { ROLES_ASISTENTE, useServicioAsistente } from "./estadoChat";

// Pagina del asistente. Sin props: toma el rol de la sesion.
export default function PaginaAsistente() {
  const { rol } = useAuth();
  const servicio = useServicioAsistente();
  const permitido = ROLES_ASISTENTE.includes(rol);

  return (
    <div className="flex flex-col gap-4 px-4 pb-4 pt-3 sm:px-6 sm:pb-6 sm:pt-4 lg:px-8 lg:pb-8 lg:pt-5">
      <PageHeader
        titulo="Asistente IA"
      />

      {servicio === null ? (
        <div className="h-[calc(100dvh-14rem)] min-h-[460px] animate-pulse rounded-2xl border border-slate-200 bg-white" />
      ) : !permitido || !servicio.activo ? (
        <div className="rounded-2xl border border-slate-200 bg-white">
          <EmptyState
            icon={IconoAsistente}
            title="El asistente no está disponible"
            description={
              permitido
                ? "El servicio del asistente está apagado en este momento. Inténtalo más tarde."
                : "Tu rol no tiene acceso al asistente virtual."
            }
          />
        </div>
      ) : (
        <section
          aria-label="Asistente virtual"
          className="h-[calc(100dvh-14rem)] min-h-[460px] rounded-2xl border border-slate-200 bg-canvas shadow-sm lg:h-[calc(100dvh-12rem)]"
        >
          <ChatAsistente modo="pagina" servicio={servicio} />
        </section>
      )}
    </div>
  );
}
