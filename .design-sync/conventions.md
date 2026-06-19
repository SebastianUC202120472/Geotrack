# GeoTrack UI Kit — convenciones

Kit de UI del panel admin de GeoTrack (SIOL · SAVA). React 19 + Tailwind 4.
Todos los componentes se importan desde `window.GeoTrackUI.*` (bundle en
`_ds_bundle.js`). Idioma del producto: **español**.

## Setup / wrapping

**No hace falta ningún provider ni wrapper.** Los componentes se renderizan
solos; los estilos viven en `_ds_bundle.css` (utilidades Tailwind compiladas) y
los tokens en `styles.css` (`@import` de fuentes + `_ds_bundle.css`). Carga
`styles.css` una vez en la raíz del documento y la tipografía de marca
**Inter Variable** (`--font-sans`) y los tokens quedan disponibles. Fondo de
lienzo del panel: `#f8fafc` (slate-50); texto base: slate-700.

## Cómo se da estilo: por PROPS, no por className

Cada componente expone su lenguaje visual mediante props; **no** se estilizan
con clases utilitarias sueltas. `className` solo se usa para ajustes de
maquetación (márgenes, ancho). Props clave:

- **Button** — `variant`: `primary` | `secondary` | `ghost` | `danger`;
  `size`: `sm` | `md` | `lg`; `icon` (componente lucide-react); `block`.
- **Badge** — `tono`: `neutral` | `info` | `brand` | `success` | `warning` | `danger`.
  **EstadoBadge** — `estado` (código como `"EN_RUTA"`, `"ENTREGADO"`, `"FALLIDO"`);
  él solo elige color y punto.
- **StatCard** — `label`, `value`, `icon`, `tone` (`brand|info|success|warning|danger`),
  `progress` (0–100), `progressLabel`, `hint`.
- **Card** — `title`, `subtitle`, `action` (nodo a la derecha), `hover`.
- **Input** / **PasswordInput** — `label`, `hint`, `error`; Input además `as`
  (`input` | `select` | `textarea`).
- **Modal** — `open`, `onClose`, `variant` (`center` | `right`, panel lateral).
- **PageHeader** — `titulo`, `subtitulo`, y botones como `children`.

## Tokens de diseño (úsalos como clases Tailwind para tu propia maquetación)

- **Azul de marca:** `bg-brand-600` (primario), `bg-brand-700` (hover/activo),
  `bg-brand-50`/`text-brand-700` (suaves). Escala `brand-50…900`.
- **Semánticos** (fondo suave + texto fuerte): `bg-success-soft`+`text-success-strong`,
  y lo mismo para `warning`, `danger`, `info`. Color sólido: `bg-success`, `text-danger`, etc.
- **Neutros:** escala `slate` de Tailwind (`text-slate-700`, `border-slate-200`, `bg-slate-50`).
- **Radios:** `rounded-card` (tarjetas), `rounded-chip` (chips de icono), `rounded-xl`
  (botones/inputs), `rounded-full` (badges/puntos).
- **Sombras:** `shadow-card` (superficies) y `shadow-card-hover` (elevación al pasar el cursor).

## Dónde está la verdad

Lee `styles.css` y sus `@import` (`_ds_bundle.css`, `fonts/fonts.css`) antes de
estilizar; cada componente trae su contrato en `<Nombre>.d.ts` y su uso en
`<Nombre>.prompt.md`.

## Ejemplo idiomático

```tsx
// Una tarjeta de ruta con cabecera, acción y KPIs. Maquetación con utilidades
// del sistema; los componentes se configuran por props.
<Card title="Ruta Miraflores" subtitle="8 paradas · Juan Pérez"
      action={<Button size="sm" variant="secondary">Ver ruta</Button>}>
  <div className="grid grid-cols-2 gap-4">
    <StatCard label="Entregados" value={128} tone="success" progress={82} />
    <StatCard label="Pendientes" value={28} tone="warning" progress={18} />
  </div>
  <div className="mt-4 flex items-center gap-2">
    <EstadoBadge estado="EN_RUTA" />
    <Button variant="primary" size="sm">Asignar</Button>
  </div>
</Card>
```
