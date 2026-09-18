// Bloques de ayuda que solo aparecen en modo demostración: muestran dentro del propio
// portal las credenciales de las empresas y los códigos de pedido sembrados, para poder
// enseñarlos y tipearlos durante una demostración sin tener una hoja aparte.
// Los datos llegan del backend (endpoint /portal/demo) y solo existen si la bandera
// PORTAL_OTP_DEMO está encendida; aquí no hay nada hardcodeado.

// Caja ámbar común a los dos bloques. Input: título, texto de apoyo e hijos.
function Caja({ titulo, apoyo, children }) {
  return (
    <div
      style={{
        margin: "18px 0 0",
        padding: "14px 16px",
        borderRadius: 14,
        background: "#fff7e6",
        border: "1.5px solid #f0c36d",
        animation: "aparecer .4s ease both",
      }}
    >
      <p style={{ margin: 0, fontSize: 12, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "#8a6410" }}>
        Modo demostración · {titulo}
      </p>
      {apoyo && (
        <p style={{ margin: "6px 0 0", fontSize: 12.5, lineHeight: 1.55, color: "#7a5a12" }}>{apoyo}</p>
      )}
      {children}
    </div>
  );
}

// Celda monoespaciada clicable que copia su valor al campo. Input: texto y handler.
function Dato({ valor, onUsar, titulo }) {
  return (
    <button
      type="button"
      onClick={onUsar}
      title={titulo}
      style={{
        border: "1px solid rgba(138,100,16,.25)",
        background: "#fffdf7",
        cursor: onUsar ? "pointer" : "default",
        borderRadius: 8,
        padding: "4px 8px",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: 12.5,
        color: "#5c4206",
        whiteSpace: "nowrap",
      }}
    >
      {valor}
    </button>
  );
}

// AyudaEmpresas: tabla de empresas con su código y clave. Al hacer clic en una fila se
// rellenan los campos de acceso. Input: lista de empresas y el handler onElegir(cod, clave).
export function AyudaEmpresas({ empresas, onElegir }) {
  if (!empresas || !empresas.length) return null;
  return (
    <Caja titulo="credenciales de prueba" apoyo="Haga clic en una empresa para rellenar el formulario, o tipéela a mano.">
      <div style={{ margin: "10px 0 0", display: "grid", gap: 6 }}>
        {empresas.map((e) => (
          <div key={e.codigo} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ flex: "1 1 150px", fontSize: 13, fontWeight: 600, color: "#5c4206" }}>{e.nombre}</span>
            <Dato valor={e.codigo} titulo="Usar esta empresa" onUsar={() => onElegir(e.codigo, e.clave)} />
            <Dato valor={e.clave} titulo="Usar esta empresa" onUsar={() => onElegir(e.codigo, e.clave)} />
          </div>
        ))}
      </div>
    </Caja>
  );
}

// AyudaPedidos: códigos de ejemplo por empresa y estado, con los últimos 4 del DNI que
// pide la verificación. Input: lista de pedidos y el handler onElegir(codigo).
export function AyudaPedidos({ pedidos, onElegir }) {
  if (!pedidos || !pedidos.length) return null;
  return (
    <Caja
      titulo="pedidos de prueba"
      apoyo="Un pedido por empresa y estado. El código de SAVA y el de la tienda llevan al mismo envío; DNI = los 4 dígitos que pide la verificación."
    >
      <div style={{ margin: "10px 0 0", maxHeight: 260, overflowY: "auto", display: "grid", gap: 6 }}>
        {pedidos.map((p) => (
          <div key={p.codigo} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ flex: "1 1 140px", fontSize: 12.5, color: "#7a5a12" }}>
              {p.retail} · <strong style={{ color: "#5c4206" }}>{p.estado}</strong>
            </span>
            <Dato valor={p.codigo} titulo="Rastrear con el código de SAVA" onUsar={() => onElegir(p.codigo)} />
            <Dato valor={p.referencia} titulo="Rastrear con el código de la tienda" onUsar={() => onElegir(p.referencia)} />
            <span style={{ fontSize: 12, color: "#8a6410" }}>DNI {p.dni}</span>
          </div>
        ))}
      </div>
    </Caja>
  );
}
