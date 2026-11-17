import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useEfectosScroll } from "../../hooks/useEfectosScroll";
import { crearTx } from "./i18n";
import NavBarLanding from "./secciones/NavBarLanding";
import Hero from "./secciones/Hero";
import Marcas from "./secciones/Marcas";
import ComoFunciona from "./secciones/ComoFunciona";
import Contadores from "./secciones/Contadores";
import Cobertura from "./secciones/Cobertura";
import SeccionGeoTrack from "./secciones/SeccionGeoTrack";
import Nosotros from "./secciones/Nosotros";
import Reclamos from "./secciones/Reclamos";
import Contacto from "./secciones/Contacto";
import FooterLanding from "./secciones/FooterLanding";
import "./landing.css";

// Asistente de atención al cliente con IA (módulo aparte, carga diferida): si su servicio está apagado no se muestra.
const WidgetAtencion = lazy(() => import("../../modulos/atencion/WidgetAtencion"));

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
      <Hero tx={tx} lang={lang} />
      <Marcas tx={tx} />
      <ComoFunciona tx={tx} />
      <Contadores tx={tx} />
      <Cobertura tx={tx} />
      <SeccionGeoTrack tx={tx} />
      <Nosotros tx={tx} />
      <Reclamos tx={tx} />
      <Contacto tx={tx} />
      <FooterLanding tx={tx} />
      <Suspense fallback={null}>
        <WidgetAtencion lang={lang} pagina="landing" />
      </Suspense>
    </div>
  );
}
