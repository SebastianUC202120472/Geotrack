import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginAdmin } from "../services/api";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      await loginAdmin(email, password);
      // Redirección fluida sin recarga completa
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex min-h-screen items-center justify-center bg-linear-to-br from-slate-900 via-indigo-950 to-slate-950 px-4">
      <div className="w-full max-w-md transform overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-8 shadow-2xl backdrop-blur-xl transition-all duration-300">
        
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-linear-to-tr from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white">GEOTRACK</h2>
          <p className="mt-2 text-sm text-slate-400">Panel de Administración SIOL-SAVA</p>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400 animate-pulse">
            <span>{error}</span>
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Correo Electrónico
            </label>
            <input
              type="email"
              required
              autoFocus
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ejemplo@geotrack.com"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/50 px-4 py-3.5 text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Contraseña
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/50 px-4 py-3.5 text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-linear-to-r from-blue-600 to-indigo-600 py-3.5 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
          >
            {loading ? "Autenticando..." : "Iniciar Sesión"}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Uso restringido a personal autorizado.
        </div>
      </div>
    </div>
  );
}