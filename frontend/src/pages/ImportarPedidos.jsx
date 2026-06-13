import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, ArrowRight, FileSpreadsheet } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";

import { subirPedidosExcel } from "../services/api";

export default function ImportarPedidos() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  const elegirArchivo = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      setFile(archivo);
      setError("");
      setResultado(null);
    }
  };

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
      <PageHeader
        titulo="Importar Pedidos"
        subtitulo="Carga un Excel (.xlsx); los pedidos se geocodifican automáticamente al subir."
      />

      <Card>
        <div className="rounded-xl border-2 border-dashed border-slate-200 p-10 text-center transition-colors hover:border-brand-400">
          <input id="excel" type="file" accept=".xlsx,.xls" className="hidden" onChange={elegirArchivo} />
          <label htmlFor="excel" className="cursor-pointer">
            <UploadCloud className={`mx-auto ${file ? "text-brand-600" : "text-slate-400"}`} size={56} />
            <p className="mt-4 text-lg font-semibold text-slate-800">
              {file ? file.name : "Selecciona o arrastra tu archivo"}
            </p>
            <p className="mt-1 text-sm text-slate-500">Formatos permitidos: XLSX, XLS</p>
          </label>
        </div>

        <Button onClick={subir} disabled={!file || cargando} size="lg" block icon={cargando ? undefined : FileSpreadsheet} className="mt-6">
          {cargando ? (<><Loader2 className="animate-spin" size={20} /> Procesando carga…</>) : "Importar datos"}
        </Button>
      </Card>

      {resultado && (
        <Card className="border-success/30">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div className="flex items-center gap-4">
              <span className="rounded-full bg-success-soft p-3 text-success"><CheckCircle2 size={26} /></span>
              <div>
                <h3 className="text-base font-semibold text-slate-900">Importación exitosa</h3>
                <p className="text-sm text-slate-500">
                  {resultado.pedidos_nuevos} pedidos registrados · {resultado.pedidos_geocodificados} geocodificados
                  {resultado.pedidos_fallidos > 0 && ` · ${resultado.pedidos_fallidos} sin ubicar`}.
                </p>
              </div>
            </div>
            <Button variant="secondary" icon={ArrowRight} onClick={() => navigate("/agrupacion")}>
              Ver agrupación por zonas
            </Button>
          </div>
        </Card>
      )}

      {error && (
        <Card className="border-danger/30">
          <div className="flex items-center gap-3 text-danger-strong">
            <AlertCircle size={22} /> <span className="font-medium">{error}</span>
          </div>
        </Card>
      )}
    </div>
  );
}
