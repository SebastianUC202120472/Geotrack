import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LogIn } from "lucide-react";
import { loginAdmin } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Logo from "../components/ui/Logo";
import EscenaReparto from "../components/EscenaReparto";
import Input from "../components/ui/Input";
import PasswordInput from "../components/ui/PasswordInput";
import Button from "../components/ui/Button";

// Pantalla de login admin. Valida credenciales y redirige al destino original.
export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { iniciarSesion } = useAuth();

  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const destino = location.state?.from?.pathname || "/";

  // Envia credenciales al backend. Recibe el evento del formulario.
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const datos = await loginAdmin(correo, password);
      iniciarSesion(datos.access_token);
      navigate(destino, { replace: true });
    } catch (err) {
      setError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen w-full lg:grid lg:grid-cols-2">
      <div
        className="relative hidden flex-col justify-between overflow-hidden p-12 text-white lg:flex"
        style={{ background: "radial-gradient(130% 130% at 0% 0%, #2b3545 0%, #161c26 65%)" }}
      >
        <EscenaReparto />
        <div className="relative z-10"><Logo light size="lg" /></div>
        <div className="relative z-10">
          <h2 className="text-3xl font-bold leading-tight">
            En ruta, en tiempo real.
          </h2>
          <p className="mt-4 max-w-md text-slate-400">
            Importa pedidos, arma rutas, asigna conductores y haz seguimiento de
            tu flota en tiempo real desde un solo panel.
          </p>
        </div>
        <p className="relative z-10 text-xs text-slate-500">© SAVA S.A.C — GeoTrack</p>
      </div>

      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 lg:min-h-0">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <div className="rounded-card border border-slate-200 bg-white p-8 shadow-card">
            <h1 className="text-2xl font-bold text-slate-900">Iniciar sesión</h1>
            <p className="mt-1 text-sm text-slate-500">
              Panel de administración GeoTrack
            </p>

            {error && (
              <div className="mt-6 rounded-xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger-strong">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
              <Input
                label="Correo electrónico"
                type="email"
                required
                autoFocus
                autoComplete="email"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                placeholder="admin@siol.com"
              />
              <PasswordInput
                label="Contraseña"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
              <Button type="submit" block size="lg" icon={LogIn} disabled={cargando}>
                {cargando ? "Autenticando…" : "Iniciar sesión"}
              </Button>
            </form>

            <p className="mt-6 text-center text-xs text-slate-400">
              Uso restringido a personal autorizado.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
