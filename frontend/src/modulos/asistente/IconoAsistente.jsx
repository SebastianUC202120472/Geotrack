// Icono propio del asistente GeoTrack: un pin de mapa (la marca) con una chispa
// dentro (la IA) y un tramo de ruta punteado. Usa currentColor, asi toma el color
// del boton o del menu donde se pinte. Recibe size, className y title opcionales.
export default function IconoAsistente({ size = 24, className = "", title, strokeWidth = 1.8 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
    >
      {title && <title>{title}</title>}
      {/* Pin de ubicacion */}
      <path d="M11 2.75c-4.28 0-7.5 3.2-7.5 7.3 0 4.9 5.86 10.07 6.8 10.87a1.07 1.07 0 0 0 1.4 0c.94-.8 6.8-5.97 6.8-10.87 0-4.1-3.22-7.3-7.5-7.3Z" />
      {/* Chispa de IA dentro del pin */}
      <path
        d="M11 6.4l.98 2.42L14.4 9.8l-2.42.98L11 13.2l-.98-2.42L7.6 9.8l2.42-.98Z"
        fill="currentColor"
        strokeWidth={1}
      />
      {/* Tramo de ruta hacia el siguiente punto */}
      <path d="M17.6 17.2c1.5-.5 2.6-1.4 3.1-2.6" strokeDasharray="0.1 2.4" strokeWidth={2} />
      <circle cx="21" cy="12.6" r="1.05" fill="currentColor" stroke="none" />
    </svg>
  );
}
