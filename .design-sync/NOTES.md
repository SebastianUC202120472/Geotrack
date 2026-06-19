# Notas de design-sync — GeoTrack UI Kit

Proyecto claude.ai/design: **GeoTrack UI Kit** (`ae3134fa-dcb9-44b8-a365-80ea7719b5c4`).

## Qué se sincroniza

GeoTrack es una **app** (SPA con Vite), no una librería de componentes. La
superficie sincronizada es el kit de UI reutilizable en
`frontend/src/components/ui/` — 12 componentes:
Badge, EstadoBadge, Button, Card, Input, Logo, Modal, PageHeader, PasswordInput,
Skeleton, SkeletonStat, StatCard. El resto de `frontend/src/components/` está
acoplado a routing/context/services y no renderiza aislado — queda fuera a
propósito.

## Pipeline (importante para re-sync)

1. **Pre-build obligatorio (`cfg.buildCmd`).** El empaquetador IIFE del conversor
   usa JSX clásico, pero el código fuente usa el runtime automático sin
   `import React`. Por eso `cfg.buildCmd` pre-empaqueta `.design-sync/ds-entry.jsx`
   (barril que reexporta los 12 componentes) a `frontend/.ds-dist/index.mjs` con
   esbuild `--jsx=automatic`, externalizando react. `cfg.entry` apunta a ese
   archivo. **Hay que correr `buildCmd` antes del conversor en cada re-sync.**
2. Conversor: `node .ds-sync/package-build.mjs --config .design-sync/config.json
   --node-modules frontend/node_modules --entry frontend/.ds-dist/index.mjs --out ./ds-bundle`.

## Decisiones / gotchas

- **`cfg.cssEntry` apunta a un archivo con hash** (`dist/assets/index-*.css`,
  salida de `vite build`). **El hash cambia en cada build del frontend** → si se
  reconstruye el frontend, actualizar `cfg.cssEntry` al nuevo nombre. Es el
  riesgo de re-sync más probable.
- **Fuentes (Inter):** la CSS compilada referencia las woff2 con rutas absolutas
  `/assets/...` que el extractor no resuelve. Se arregla con
  `cfg.extraFonts` → `@fontsource-variable/inter/wght.css` (url() relativas +
  woff2 al lado). No quitar.
- **Sin `.d.ts` en el repo** (es JSX): los contratos de props vienen de
  `cfg.dtsPropsFor` (escritos a mano leyendo el fuente). Si cambian las props de
  un componente, actualizar `dtsPropsFor`.
- **Captura sin prefers-reduced-motion:** los componentes animados pueden
  capturarse a mitad de animación.
  - `StatCard`: las previews pasan `value` como **string** para mostrar el número
    final determinista (con `number` el contador animado salía a ~99%).
  - `Modal`: la variante `variant="right"` (panel lateral) **no se previsualiza**
    — su animación de entrada y su posición al borde derecho no se capturan de
    forma fiable. Está soportada y documentada en `Modal.d.ts`/convenciones.
- **`Skeleton`:** solo acepta `className` para dimensionar, así que las previews
  usan únicamente clases Tailwind que el sistema ya compila (`h-8 w-20`,
  `h-3 w-full`, `h-1.5 w-full`, `rounded-card/full`). No inventar clases nuevas:
  Tailwind 4 (JIT) solo compila las que la app usa.

## Known render warns (esperados, no son nuevos)

- `[RENDER_THIN]` en `Modal` — altura medida 0px: es `position: fixed`, el root
  no aporta altura. Benigno; el diálogo sí renderiza (ver captura).

## Riesgos de re-sync (vigilar)

- **Hash de `cssEntry`:** se rompe al reconstruir el frontend (ver arriba).
- **`dtsPropsFor` se mantiene a mano:** se desactualiza si cambian las props en
  `frontend/src/components/ui/*.jsx`.
- **Pre-build:** si no se corre `cfg.buildCmd` antes del conversor, `frontend/.ds-dist/`
  queda viejo y se sincroniza una versión obsoleta.
- **`@fontsource-variable/inter`:** si se cambia la fuente del proyecto, ajustar
  `cfg.extraFonts`.
- **`frontend/dist/` está gitignored:** en un clon nuevo hay que correr
  `cd frontend && npm run build` para regenerar `dist/assets/*.css` (la fuente de
  `cssEntry`) y luego actualizar el hash en `cfg.cssEntry`.
