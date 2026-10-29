// Pruebas del aviso al optimizar la ruta (C20-01, C20-03).
jest.mock("@/api/rutas", () => ({ optimizarRuta: jest.fn() }));

import { mensajeOptimizacion } from "@/services/routeService";

describe("mensaje al optimizar", () => {
  it("muestra km estimados y el ahorro", () => {
    const m = mensajeOptimizacion({ mensaje: "", total_paradas: 4, km_estimado: 12.34, km_ahorrado: 2.5 });
    expect(m).toContain("Se ordenaron 4 paradas");
    expect(m).toContain("12.3 km");
    expect(m).toContain("Ahorras 2.5 km");
  });

  it("avisa las paradas sin ubicación con sus códigos", () => {
    const m = mensajeOptimizacion({ mensaje: "", total_paradas: 3, paradas_sin_ubicacion: 1, codigos_sin_ubicacion: ["PD-009"] }, "puntos de recojo");
    expect(m).toContain("3 puntos de recojo");
    expect(m).toContain("1 parada no tiene ubicación");
    expect(m).toContain("PD-009");
  });

  it("sin km no inventa el recorrido", () => {
    expect(mensajeOptimizacion({ mensaje: "", total_paradas: 2 })).not.toContain("km");
  });
});
