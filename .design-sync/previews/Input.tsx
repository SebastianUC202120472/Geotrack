// Previews del campo de formulario: estados (normal con ayuda, error), y la
// variante select. Etiquetas y textos realistas del panel.
import { Input } from "frontend-geotrack";

const col = { display: "flex", flexDirection: "column" as const, gap: 16, maxWidth: 360 };

export const ConAyuda = () => (
  <div style={col}>
    <Input label="Nombre del conductor" placeholder="Ej. Juan Pérez" hint="Como aparecerá en la app móvil" />
  </div>
);

export const ConError = () => (
  <div style={col}>
    <Input label="Correo electrónico" defaultValue="correo-invalido" error="Ingresa un correo válido" />
  </div>
);

export const Select = () => (
  <div style={col}>
    <Input label="Zona de reparto" as="select" defaultValue="miraflores">
      <option value="miraflores">Miraflores</option>
      <option value="surco">Santiago de Surco</option>
      <option value="sanisidro">San Isidro</option>
    </Input>
  </div>
);

export const Textarea = () => (
  <div style={col}>
    <Input label="Observaciones" as="textarea" rows={3} placeholder="Notas para el conductor…" />
  </div>
);
