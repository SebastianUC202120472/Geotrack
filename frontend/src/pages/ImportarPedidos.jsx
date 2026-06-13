import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileSpreadsheet, UploadCloud, CheckCircle, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import Header from "../components/Header";
import { subirPedidosExcel } from "../services/api";

export default function ImportarPedidos() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      setFile(archivo);
      setError("");
      setResultado(null);
    }
  };

  const subirArchivo = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const response = await subirPedidosExcel(file);
      setResultado(response);
    } catch (err) {
      setError(err.message || "Error al procesar el archivo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 flex flex-col">
      <Header />
      
      {/* Contenedor principal que llena el espacio restante */}
      <main className="flex-grow p-8 flex flex-col">
        <div className="w-full h-full flex flex-col space-y-6">
          
          {/* Título */}
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <h1 className="text-3xl font-extrabold text-slate-900">Importar Pedidos</h1>
            <p className="text-slate-500 mt-2">Carga tu archivo Excel (.xlsx) para registrar múltiples pedidos.</p>
          </div>

          {/* Área de Upload que crece para llenar el alto */}
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm flex-grow flex flex-col justify-center">
            <div className="border-2 border-dashed border-slate-300 rounded-2xl p-16 text-center hover:border-blue-500 transition-colors flex-grow flex flex-col justify-center items-center">
              <input id="excel" type="file" accept=".xlsx,.xls" className="hidden" onChange={handleFileChange} />
              <label htmlFor="excel" className="cursor-pointer">
                <UploadCloud className={`mx-auto ${file ? "text-blue-600" : "text-slate-400"}`} size={80} />
                <h2 className="mt-6 text-2xl font-bold text-slate-800">
                  {file ? file.name : "Selecciona o arrastra tu archivo"}
                </h2>
                <p className="text-slate-500 mt-2 text-lg">Formatos permitidos: XLSX, XLS</p>
              </label>
            </div>

            <button
              onClick={subirArchivo}
              disabled={!file || loading}
              className={`mt-8 w-full py-6 rounded-2xl text-xl font-bold flex items-center justify-center gap-3 transition-all ${
                !file || loading ? "bg-slate-300 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-200"
              }`}
            >
              {loading ? (
                <> <Loader2 className="animate-spin" /> Procesando carga... </>
              ) : (
                <> <FileSpreadsheet size={24} /> Importar Datos </>
              )}
            </button>
          </div>

          {/* Feedback */}
          {(resultado || error) && (
            <div className={`p-6 rounded-2xl shadow-sm ${resultado ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
              {resultado ? (
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-4">
                    <CheckCircle className="text-green-600" size={32} />
                    <div>
                      <h2 className="font-bold text-green-800 text-lg">Importación exitosa</h2>
                      <p className="text-green-600">Se han registrado los nuevos pedidos correctamente.</p>
                    </div>
                  </div>
                  <button onClick={() => navigate("/geocodificacion")} className="bg-slate-900 text-white px-8 py-4 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-800 transition">
                    Ir a Geocodificación <ArrowRight size={20} />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-4 text-red-700">
                  <AlertCircle size={32} />
                  <span className="font-medium text-lg">{error}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}