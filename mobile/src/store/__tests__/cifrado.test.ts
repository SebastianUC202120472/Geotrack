// Pruebas del cifrado local de la cola offline y la copia de la ruta (EX-23).
jest.mock("expo-secure-store", () => {
  const datos: Record<string, string> = {};
  return {
    getItemAsync: jest.fn(async (k: string) => datos[k] ?? null),
    setItemAsync: jest.fn(async (k: string, v: string) => { datos[k] = v; }),
  };
});
jest.mock("expo-crypto", () => ({
  getRandomBytes: (n: number) => Uint8Array.from({ length: n }, () => Math.floor(Math.random() * 256)),
}));

import { cifrar, descifrar } from "@/store/cifrado";

describe("cifrado local", () => {
  it("cifra y descifra sin dejar el texto a la vista", async () => {
    const texto = JSON.stringify([{ pedidoId: 9, receptorNombre: "Luis Rojas", receptorDocumento: "45678912" }]);
    const guardado = await cifrar(texto);
    expect(guardado.startsWith("v1:")).toBe(true);
    expect(guardado).not.toContain("Luis");
    expect(await descifrar(guardado)).toBe(texto);
  });

  it("usa un nonce distinto en cada cifrado", async () => {
    expect(await cifrar("hola")).not.toBe(await cifrar("hola"));
  });

  it("lee los datos que quedaron sin cifrar de la versión anterior", async () => {
    expect(await descifrar('[{"pedidoId":1}]')).toBe('[{"pedidoId":1}]');
  });

  it("no acepta un texto alterado", async () => {
    const guardado = await cifrar("dato");
    const alterado = guardado.slice(0, -4) + (guardado.endsWith("AAAA") ? "BBBB" : "AAAA");
    expect(await descifrar(alterado)).toBeNull();
  });
});
