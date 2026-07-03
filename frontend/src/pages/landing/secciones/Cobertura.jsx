import limaAerea from "../../../assets/landing/lima-aerea.jpg";

// Datos de las 5 zonas de cobertura (clave i18n del título + distritos en español,
// que la fuente no traduce). Se recorren para armar las tarjetas del grid.
const ZONAS = [
  { clave: "z1", delay: "0", distritos: "Independencia · Comas · Los Olivos · SMP · Carabayllo · Puente Piedra · Ancón" },
  { clave: "z2", delay: "70", distritos: "Cercado · Jesús María · Lince · Miraflores · San Isidro · Surquillo · San Borja" },
  { clave: "z3", delay: "140", distritos: "SJL · Santa Anita · Ate · La Molina · El Agustino · Chaclacayo" },
  { clave: "z4", delay: "210", distritos: "Surco · SJM · VMT · Villa El Salvador · Chorrillos · Lurín · Pucusana" },
  { clave: "z5", delay: "280", distritos: "Callao · Bellavista · La Perla · Ventanilla · Mi Perú" },
];
const NOMBRES_ES = { z1: "Lima Norte", z2: "Lima Centro", z3: "Lima Este", z4: "Lima Sur", z5: "Callao" };

// Cobertura (#cobertura): texto + foto de Lima con chip de 43 distritos, y grid de
// 5 tarjetas de zona con sus distritos. Input: tx (traducción).
export default function Cobertura({ tx }) {
  return (
    <section id="cobertura" data-sec="p" style={{ maxWidth: 1200, margin: "0 auto", padding: "110px 28px 0" }}>
      <div>
        <div
          data-reveal="0"
          style={{ maxWidth: 680, opacity: 0, transform: "translateY(26px)", transition: "opacity .7s ease, transform .7s ease" }}
        >
          <p data-i18n="cobE" style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, letterSpacing: ".14em", textTransform: "uppercase", color: "#2679d8" }}>
            {tx("cobE", "Cobertura")}
          </p>
          <h2 data-i18n="cobT" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(30px, 3.6vw, 44px)", lineHeight: 1.1, letterSpacing: "-.01em" }}>
            {tx("cobT", "Todo Lima, de Ancón a Pucusana.")}
          </h2>
          <p data-i18n="cobD" style={{ margin: "18px 0 0", fontSize: 16, lineHeight: 1.65, color: "#4f6580" }}>
            {tx("cobD", "Cubrimos los 43 distritos de Lima Metropolitana y el Callao con rutas diarias organizadas por zonas. Su cliente recibe su pedido viva donde viva.")}
          </p>
          <p data-i18n="cobD2" style={{ margin: "14px 0 0", fontSize: 14, lineHeight: 1.6, color: "#7288a0" }}>
            {tx("cobD2", "¿Necesita una zona con horario especial? Armamos rutas dedicadas según el volumen de su tienda.")}
          </p>
        </div>

        <div
          data-reveal="100"
          style={{
            position: "relative",
            margin: "40px 0 0",
            borderRadius: 26,
            overflow: "hidden",
            boxShadow: "0 24px 60px rgba(15,43,74,.16)",
            opacity: 0,
            transform: "translateY(26px)",
            transition: "opacity .8s ease, transform .8s ease",
          }}
        >
          <img
            src={limaAerea}
            alt="Lima desde el aire"
            style={{ width: "100%", height: "min(42vw, 400px)", objectFit: "cover", display: "block", animation: "kenburns 26s ease-in-out infinite alternate" }}
          />
          <div aria-hidden="true" style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(9,28,50,0) 40%, rgba(9,28,50,.78) 100%)" }} />
          <div style={{ position: "absolute", left: 26, bottom: 22, color: "#fff" }}>
            <p data-i18n="cobFoto1" style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: "clamp(20px, 2.4vw, 28px)" }}>
              {tx("cobFoto1", "Lima Metropolitana y Callao")}
            </p>
            <p data-i18n="cobFoto2" style={{ margin: "6px 0 0", fontSize: 14, color: "#cfe0f2" }}>
              {tx("cobFoto2", "De Ancón a Pucusana · de La Molina al Callao")}
            </p>
          </div>
          <div
            style={{
              position: "absolute",
              top: 18,
              right: 18,
              background: "rgba(255,255,255,.94)",
              backdropFilter: "blur(6px)",
              borderRadius: 99,
              padding: "10px 18px",
              display: "flex",
              alignItems: "baseline",
              gap: 6,
              boxShadow: "0 10px 26px rgba(3,15,30,.25)",
            }}
          >
            <span data-count="43" style={{ fontFamily: "Archivo, sans-serif", fontWeight: 800, fontSize: 22, color: "#2679d8" }}>0</span>
            <span data-i18n="cobChip" style={{ fontSize: 13, fontWeight: 600, color: "#0f2b4a" }}>{tx("cobChip", "distritos")}</span>
          </div>
        </div>

        <div style={{ margin: "16px 0 0", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(218px, 1fr))", gap: 14 }}>
          {ZONAS.map((z) => (
            <div
              key={z.clave}
              data-reveal={z.delay}
              className="ldg-zona-card"
              style={{
                background: "#fff",
                border: "1px solid rgba(15,43,74,.08)",
                borderRadius: 20,
                padding: "20px 24px",
                display: "flex",
                alignItems: "center",
                gap: 16,
                opacity: 0,
                transform: "translateY(26px)",
                transition: "opacity .6s ease, transform .6s ease",
              }}
            >
              <span style={{ width: 10, height: 10, borderRadius: 99, background: "#2679d8", flex: "none" }} />
              <div>
                <h3 data-i18n={z.clave} style={{ margin: 0, fontFamily: "Archivo, sans-serif", fontWeight: 700, fontSize: 16 }}>
                  {tx(z.clave, NOMBRES_ES[z.clave])}
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: 13.5, color: "#7288a0" }}>{z.distritos}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
