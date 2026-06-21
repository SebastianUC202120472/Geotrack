import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  UploadCloud,
  CheckCircle2,
  Loader2,
  ArrowRight,
  FileSpreadsheet,
  FileX2,
} from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";

import { subirPedidosExcel } from "../services/api";

export default function ImportarPedidos() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  // Guarda el archivo seleccionado y limpia estados previos
  const elegirArchivo = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      setFile(archivo);
      setError("");
      setResultado(null);
    }
  };

  // Envía el archivo al backend y almacena el resultado o el error
  const subir = async () => {
    if (!file) return;
    setCargando(true);
    setError("");
    try {
      setResultado(await subirPedidosExcel(file));
    } catch (err) {
      setError(err.message || "Error al procesar el archivo");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera de la página */}
      <div className="animate-fade-up">
        <PageHeader
          titulo="Importar Pedidos"
          subtitulo="Carga un Excel (.xlsx); los pedidos se geocodifican automáticamente al subir."
        />
      </div>

      {/* Zona de carga de archivo */}
      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        <SectionCard
          title="Archivo de pedidos"
          subtitle="Formatos permitidos: XLSX, XLS"
        >
          {/* Input oculto para selección de archivo */}
          <input
            id="excel"
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={elegirArchivo}
          />

          {/* Estado vacío: aún no se eligió archivo */}
          {!file ? (
            <label htmlFor="excel" className="block cursor-pointer">
              <EmptyState
                icon={UploadCloud}
                title="Selecciona o arrastra tu archivo"
                description="Haz clic aquí para elegir un archivo Excel con los pedidos a importar."
              />
            </label>
          ) : (
            /* Archivo seleccionado: preview con nombre */
            <label
              htmlFor="excel"
              className="block cursor-pointer rounded-xl border-2 border-dashed border-brand-300 bg-brand-50 p-8 text-center transition-colors hover:border-brand-400 hover:bg-brand-100/60"
            >
              <FileSpreadsheet
                className="mx-auto text-brand-600"
                size={48}
              />
              <p className="mt-3 text-base font-semibold text-slate-800">
                {file.name}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Haz clic para cambiar el archivo
              </p>
            </label>
          )}

          {/* Botón de importación */}
          <Button
            onClick={subir}
            disabled={!file || cargando}
            size="lg"
            block
            icon={cargando ? undefined : FileSpreadsheet}
            className="mt-5"
          >
            {cargando ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Procesando carga…
              </>
            ) : (
              "Importar datos"
            )}
          </Button>
        </SectionCard>
      </div>

      {/* Resultado exitoso */}
      {resultado && (
        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <div className="rounded-card border border-emerald-200 bg-emerald-50 p-5 shadow-card">
            <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
              <div className="flex items-center gap-4">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                  <CheckCircle2 size={24} />
                </span>
                <div>
                  <h3 className="text-base font-semibold text-slate-900">
                    Importación exitosa
                  </h3>
                  <p className="text-sm text-slate-600">
                    {resultado.pedidos_nuevos} pedidos registrados ·{" "}
                    {resultado.pedidos_geocodificados} geocodificados
                    {resultado.pedidos_fallidos > 0 &&
                      ` · ${resultado.pedidos_fallidos} sin ubicar`}
                    .
                  </p>
                </div>
              </div>
              <Button
                variant="secondary"
                icon={ArrowRight}
                onClick={() => navigate("/agrupacion")}
              >
                Ver agrupación por zonas
              </Button>
            </div>

            {/* Panel de filas rechazadas por cliente no registrado */}
            {resultado.total_rechazados > 0 && (
              <div className="mt-4 rounded-card border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-semibold text-amber-800">
                  {resultado.total_rechazados} fila(s) no se importaron: el cliente no está registrado.
                  Registra primero al cliente (Clientes) y vuelve a subir el Excel.
                </p>
                <ul className="mt-2 space-y-1 text-sm text-amber-700">
                  {resultado.rechazados.map((r, i) => (
                    <li key={i} className="nums">Fila {r.fila}: &quot;{r.cliente}&quot; — {r.motivo}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error de importación */}
      {error && (
        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <div className="rounded-card border border-red-200 bg-red-50 p-5 shadow-card">
            <div className="flex items-start gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
                <FileX2 size={20} />
              </span>
              <div>
                <h3 className="text-sm font-semibold text-red-800">
                  Error al procesar el archivo
                </h3>
                <p className="mt-0.5 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
