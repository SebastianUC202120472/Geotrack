// Pruebas de la subida de la cola offline (C26-01, C26-02, C29-01).
const cola: Record<string, unknown>[] = [];
jest.mock("@/store/colaSync", () => ({
  listar: jest.fn(async () => cola.map((i) => ({ ...i }))),
  quitar: jest.fn(async (id: string) => { const n = cola.findIndex((i) => i.id === id); if (n >= 0) cola.splice(n, 1); }),
  actualizar: jest.fn(async (id: string, cambios: Record<string, unknown>) => {
    const item = cola.find((i) => i.id === id);
    if (item) Object.assign(item, cambios);
  }),
}));
jest.mock("@/hooks/useConexion", () => ({ estaOnline: jest.fn(async () => true) }));
jest.mock("@/features/ruta/hooks", () => ({ claves: { rutaActiva: ["r"], manifiesto: ["m"], misReportes: ["rep"] } }));
const llamadas: string[] = [];
let fallarRedEn: string | null = null;
const registrar = (nombre: string, valor?: unknown) => async (...args: unknown[]) => {
  if (fallarRedEn === nombre) { fallarRedEn = null; throw { red: true }; }
  llamadas.push(`${nombre}:${JSON.stringify(args)}`);
  return valor;
};
jest.mock("@/api/conductor", () => ({
  subirEvidencia: (...a: unknown[]) => registrar("subirEvidencia")(...a),
  marcarEstadoParada: (...a: unknown[]) => registrar("marcarEstado")(...a),
  crearReporte: (...a: unknown[]) => registrar("crearReporte", { id: 77 })(...a),
  subirEvidenciaReporte: (...a: unknown[]) => registrar("fotoReporte")(...a),
}));
jest.mock("@/api/client", () => ({ esErrorDeRed: (e: { red?: boolean }) => !!e?.red }));

import { sincronizar } from "@/features/sync/sincronizador";

const qc = { invalidateQueries: jest.fn() } as unknown as Parameters<typeof sincronizar>[0];

describe("sincronización de la cola offline", () => {
  beforeEach(() => { cola.length = 0; llamadas.length = 0; fallarRedEn = null; });

  it("sube la foto con su GPS y luego entrega con quién recibió", async () => {
    cola.push({ id: "1", tipo: "ENTREGA", pedidoId: 5, fotoUri: "file://f.jpg", latitud: -12.1, longitud: -77,
      receptorNombre: "Luis Rojas", receptorDocumento: "45678912" });
    await sincronizar(qc);
    expect(llamadas[0]).toBe('subirEvidencia:[5,"file://f.jpg",{"latitud":-12.1,"longitud":-77}]');
    expect(llamadas[1]).toBe('marcarEstado:[5,"ENTREGADO",null,{"nombre":"Luis Rojas","documento":"45678912"}]');
    expect(cola).toHaveLength(0);
  });

  it("una falla con foto crea el reporte y le adjunta la foto", async () => {
    cola.push({ id: "2", tipo: "FALLIDO", pedidoId: 6, motivo: "Cliente ausente", fotoUri: "file://g.jpg" });
    await sincronizar(qc);
    expect(llamadas.map((l) => l.split(":")[0])).toEqual(["marcarEstado", "crearReporte", "fotoReporte"]);
    expect(llamadas[2]).toBe('fotoReporte:[77,"file://g.jpg",null]');
  });

  it("si se corta la señal, conserva el avance y no repite lo ya hecho", async () => {
    cola.push({ id: "3", tipo: "ENTREGA", pedidoId: 7, fotoUri: "file://h.jpg",
      receptorNombre: "Ana", receptorDocumento: "12345678" });
    fallarRedEn = "marcarEstado";
    await sincronizar(qc);
    expect(cola).toHaveLength(1);
    expect(cola[0].evidenciaSubida).toBe(true);
    llamadas.length = 0;
    await sincronizar(qc);
    expect(llamadas.map((l) => l.split(":")[0])).toEqual(["marcarEstado"]);
    expect(cola).toHaveLength(0);
  });
});
