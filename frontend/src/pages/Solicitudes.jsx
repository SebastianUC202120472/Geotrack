import PageHeader from "../components/ui/PageHeader";
import FormAceptarSolicitud from "../components/FormAceptarSolicitud";

// Pantalla de aceptación de solicitudes de recojo.
// Delega el formulario al componente reutilizable FormAceptarSolicitud.
export default function Solicitudes() {
  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera de la página */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Aceptar solicitud de recojo"
          subtitulo="Elige el cliente, sube el Excel de pedidos y registra el recojo en el sistema."
        />
      </div>

      {/* Formulario de aceptación */}
      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        <FormAceptarSolicitud />
      </div>
    </div>
  );
}
