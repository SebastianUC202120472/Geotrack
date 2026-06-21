// Previews del campo de contraseña: estado normal (con texto oculto y botón de
// ojo) y estado de error.
import { PasswordInput } from "frontend-geotrack";

const col = { display: "flex", flexDirection: "column" as const, gap: 16, maxWidth: 360 };

export const Normal = () => (
  <div style={col}>
    <PasswordInput label="Contraseña" defaultValue="supersecreto" hint="Mínimo 8 caracteres" />
  </div>
);

export const ConError = () => (
  <div style={col}>
    <PasswordInput label="Contraseña" defaultValue="123" error="La contraseña es demasiado corta" />
  </div>
);
