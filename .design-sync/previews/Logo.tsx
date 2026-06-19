// Previews del logo. En el entorno de previsualización no existe /logo.png, así
// que se muestra el monograma de respaldo (la letra G + el wordmark), que es
// justo el caso que conviene documentar.
import { Logo } from "frontend-geotrack";

export const SobreClaro = () => (
  <div style={{ padding: 8 }}>
    <Logo />
  </div>
);

export const SobreOscuro = () => (
  <div style={{ background: "#0f172a", padding: 24, borderRadius: 12, display: "inline-block" }}>
    <Logo light />
  </div>
);

export const SoloMonograma = () => (
  <div style={{ padding: 8 }}>
    <Logo wordmark={false} />
  </div>
);
