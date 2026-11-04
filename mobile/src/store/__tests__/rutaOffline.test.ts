// Pruebas de la copia de la ruta para abrirla sin señal (C27-02).
jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock")
);
jest.mock("@/store/cifrado", () => ({
  cifrar: async (t: string) => `x:${t}`,
  descifrar: async (t: string) => (t.startsWith("x:") ? t.slice(2) : t),
}));
jest.mock("@/api/client", () => ({
  esErrorDeRed: (e: { red?: boolean }) => !!e?.red,
}));

import AsyncStorage from "@react-native-async-storage/async-storage";
import { conCopiaOffline, ajustarCopia, limpiarRutaOffline } from "@/store/rutaOffline";

const esperar = () => new Promise((r) => setTimeout(r, 0));

describe("copia offline de la ruta", () => {
  beforeEach(() => AsyncStorage.clear());

  it("sin señal devuelve la última ruta descargada", async () => {
    await conCopiaOffline("manifiesto", async () => ({ paradas: [{ pedido_id: 1, estado_entrega: "PENDIENTE" }] }))();
    await esperar();
    const sinRed = conCopiaOffline("manifiesto", async () => { throw { red: true }; });
    await expect(sinRed()).resolves.toEqual({ paradas: [{ pedido_id: 1, estado_entrega: "PENDIENTE" }] });
  });

  it("si el servidor dice que ya no hay ruta (404) borra la copia", async () => {
    await conCopiaOffline("ruta-activa", async () => ({ ruta_id: 3 }))();
    await esperar();
    await expect(conCopiaOffline("ruta-activa", async () => { throw { response: { status: 404 } }; })()).rejects.toBeTruthy();
    await esperar();
    await expect(conCopiaOffline("ruta-activa", async () => { throw { red: true }; })()).rejects.toBeTruthy();
  });

  it("una entrega hecha sin señal queda en la copia", async () => {
    await conCopiaOffline("manifiesto", async () => ({ paradas: [{ pedido_id: 1, estado_entrega: "PENDIENTE" }] }))();
    await esperar();
    await ajustarCopia<{ paradas: { pedido_id: number; estado_entrega: string }[] }>("manifiesto", (m) => ({
      paradas: m.paradas.map((p) => ({ ...p, estado_entrega: "ENTREGADO" })),
    }));
    const copia = await conCopiaOffline("manifiesto", async () => { throw { red: true }; })();
    expect(copia).toEqual({ paradas: [{ pedido_id: 1, estado_entrega: "ENTREGADO" }] });
  });

  it("al cerrar sesión no queda ninguna copia", async () => {
    await conCopiaOffline("navegacion", async () => ({ paradas: [] }))();
    await esperar();
    await limpiarRutaOffline();
    expect(await AsyncStorage.getAllKeys()).toEqual([]);
  });
});
