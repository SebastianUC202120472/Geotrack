# Crea por la API los 4 vehiculos y 4 conductores que exige backend/scripts/preparar_demo.py
# (seed_portal_demo.CORREOS_CONDUCTORES), cada conductor con su vehiculo asignado.
# Es idempotente: si el vehiculo o el conductor ya existen, no los duplica; solo corrige la
# asignacion si hace falta. Del .env solo lee ADMIN_EMAIL y ADMIN_PASSWORD.
#
# Uso (desde la raiz del repo, con docker compose levantado):
#   python asistente/scripts/crear_conductores.py
#   python asistente/scripts/crear_conductores.py --url http://localhost:8080 --clave-conductores "Otra2026!"
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comun import URL_BASE_POR_DEFECTO, ErrorApi, iniciar_sesion, peticion, preparar_consola  # noqa: E402

# Mismo orden que CORREOS_CONDUCTORES en backend/scripts/seed_portal_demo.py.
CONDUCTORES = (
    {"correo": "juan@prueba.com", "nombre": "Juan Pérez", "placa": "ABC-101"},
    {"correo": "rosa.medina@sava.pe", "nombre": "Rosa Medina", "placa": "ABC-102"},
    {"correo": "luis.chavez@sava.pe", "nombre": "Luis Chávez", "placa": "ABC-103"},
    {"correo": "marta.silva@sava.pe", "nombre": "Marta Silva", "placa": "ABC-104"},
)
VEHICULO_BASE = {"marca": "Hyundai H100", "capacidad_volumetrica": 8.0, "capacidad_cajas": 120, "estado": "DISPONIBLE"}
# Contrasena de prueba para la app movil (cumple la politica: mayuscula, minuscula, numero y simbolo).
CLAVE_CONDUCTORES = "Conductor2026!"


def asegurar_vehiculo(url: str, token: str, placa: str, vehiculos: dict) -> dict:
    """Devuelve el vehiculo con esa placa; lo crea sin conductor si no existe. Recibe url, token, placa y el indice por placa."""
    if placa in vehiculos:
        print(f"  = Vehículo {placa} ya existe.")
        return vehiculos[placa]
    vehiculo = peticion("POST", f"{url}/api/vehiculos/", token, datos={"placa": placa, **VEHICULO_BASE})
    vehiculos[placa] = vehiculo
    print(f"  + Vehículo {placa} creado.")
    return vehiculo


def asegurar_conductor(url: str, token: str, datos: dict, vehiculo: dict, conductores: dict, clave: str) -> None:
    """Crea el conductor con su vehiculo, o si ya existe le asigna el vehiculo si no lo tiene.
    Recibe url, token, datos del conductor, su vehiculo, el indice por correo y la clave."""
    correo, placa = datos["correo"], datos["placa"]
    existente = conductores.get(correo)
    if existente is None:
        libre = vehiculo.get("conductor_id") is None
        cuerpo = {"correo": correo, "contrasena": clave, "nombre": datos["nombre"]}
        if libre:
            cuerpo["vehiculo_id"] = vehiculo["id"]
        nuevo = peticion("POST", f"{url}/api/conductores/", token, datos=cuerpo)
        print(f"  + Conductor {correo} ({datos['nombre']}) creado.")
        if libre:
            return
        existente = nuevo  # el vehiculo lo tenia otro: se reasigna abajo
    asignado = (existente.get("vehiculo") or {}).get("placa")
    if asignado == placa:
        print(f"  = Conductor {correo} ya existe con {placa}.")
        return
    peticion("PATCH", f"{url}/api/vehiculos/{vehiculo['id']}", token, datos={"conductor_id": existente["usuario_id"]})
    print(f"  ~ {placa} asignado a {correo}" + (f" (antes tenía {asignado})." if asignado else "."))


def main() -> int:
    """Crea los vehiculos y conductores de la demo. Devuelve el codigo de salida."""
    preparar_consola()
    parser = argparse.ArgumentParser(description="Crea los 4 conductores y vehículos que exige preparar_demo.py.")
    parser.add_argument("--url", default=URL_BASE_POR_DEFECTO, help="URL de Nginx (por defecto %(default)s)")
    parser.add_argument("--env", default=None, help="Ruta del .env (por defecto el de la raíz del repo)")
    parser.add_argument("--clave-conductores", default=CLAVE_CONDUCTORES,
                        help="Contraseña de los conductores NUEVOS (por defecto %(default)s)")
    args = parser.parse_args()
    url = args.url.rstrip("/")

    token = iniciar_sesion(url, args.env)
    vehiculos = {v["placa"]: v for v in peticion("GET", f"{url}/api/vehiculos/", token) or []}
    conductores = {c["correo"]: c for c in peticion("GET", f"{url}/api/conductores/", token) or []}

    errores = 0
    for datos in CONDUCTORES:
        print(f"{datos['nombre']} <{datos['correo']}> / {datos['placa']}")
        try:
            vehiculo = asegurar_vehiculo(url, token, datos["placa"], vehiculos)
            asegurar_conductor(url, token, datos, vehiculo, conductores, args.clave_conductores)
        except ErrorApi as exc:
            errores += 1
            print(f"  ! ERROR HTTP {exc.codigo}: {exc.detalle}")

    print()
    if errores:
        print(f"Terminó con {errores} error(es). Corrígelos en el panel y vuelve a correr el script.")
        return 1
    print("Listo: los 4 conductores tienen su vehículo.")
    print(f"Los conductores creados ahora entran a la app con la contraseña {args.clave_conductores}"
          " (los que ya existían conservan la suya).")
    print("Siguiente paso: docker exec geotrack-backend-1 python scripts/preparar_demo.py --si")
    return 0


if __name__ == "__main__":
    sys.exit(main())
