import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useEfectosScroll } from "../../hooks/useEfectosScroll";
import { crearTx } from "./i18n";
import NavBarLanding from "./secciones/NavBarLanding";
import FooterLanding from "./secciones/FooterLanding";
import "./landing.css";

// Página pública de SAVA: compone las secciones del landing en orden.
export default function Landing() {
  const [lang, setLang] = useState("es");
  const contRef = useRef(null);
  const location = useLocation();
  useEfectosScroll(contRef);

  // Título del documento y scroll al hash (#reclamos) al entrar.
  useEffect(() => {
    document.title = "SAVA S.A.C. — Entregas de última milla";
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
  }, [location.hash]);

  const tx = crearTx(lang);
  return (
    <div ref={contRef} className="ldg-pagina">
      <NavBarLanding lang={lang} setLang={setLang} tx={tx} />
      {/* Tareas 6-8 añaden aquí: Hero, Marcas, ComoFunciona, Contadores, Cobertura,
          SeccionGeoTrack, Nosotros, Reclamos, Contacto */}
      <FooterLanding tx={tx} />
    </div>
  );
}
