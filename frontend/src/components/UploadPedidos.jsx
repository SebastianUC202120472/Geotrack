import { useState } from 'react';
import { FileUp, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadPedidosExcel } from '../services/api';

export default function UploadPedidos() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'success', 'error'
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    try {
      await uploadPedidosExcel(file);
      setStatus('success');
      setMessage('¡Pedidos importados con éxito!');
    } catch (err) {
      setStatus('error');
      setMessage(err.message);
    }
  };

  return (
    <div className="p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <h2 className="text-xl font-bold text-slate-800 mb-4">Carga Masiva de Pedidos</h2>
      
      <div className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${status === 'uploading' ? 'border-blue-400 bg-blue-50' : 'border-slate-300 hover:border-blue-500'}`}>
        <input type="file" id="file-upload" className="hidden" accept=".xlsx, .xls, .csv" onChange={handleFileChange} />
        <label htmlFor="file-upload" className="cursor-pointer">
          <FileUp className={`mx-auto h-12 w-12 ${file ? 'text-blue-600' : 'text-slate-400'}`} />
          <p className="mt-2 text-sm text-slate-600 font-medium">
            {file ? file.name : "Arrastra o selecciona tu archivo Excel"}
          </p>
        </label>
      </div>

      <button 
        onClick={handleUpload}
        disabled={!file || status === 'uploading'}
        className="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-slate-300 transition-all flex items-center justify-center gap-2"
      >
        {status === 'uploading' ? <Loader2 className="animate-spin" /> : 'Procesar Importación'}
      </button>

      {/* Retroalimentación Visual */}
      {status === 'success' && (
        <div className="mt-4 p-4 bg-green-50 text-green-700 rounded-lg flex items-center gap-2">
          <CheckCircle className="h-5 w-5" /> {message}
        </div>
      )}
      {status === 'error' && (
        <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
          <AlertCircle className="h-5 w-5" /> {message}
        </div>
      )}
    </div>
  );
}