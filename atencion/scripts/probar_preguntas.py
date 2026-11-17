# Prueba el asistente de atencion con proveedores REALES de IA, por tandas, sin levantar Docker.
# Pensado para PCs donde Ollama es demasiado lento: usa solo proveedores en la nube y deja
# elegir cuales y que rango de preguntas correr, para repartir la cuota gratuita entre tandas.
#
# Lee las claves del .env de la RAIZ del repositorio (no las imprime). Usa una base SQLite
# temporal: no toca la base del sistema. Solo preguntas de prueba, sin datos reales.
#
# Uso (desde atencion/):
#   python scripts/probar_preguntas.py                         # todas, orden de ATENCION_PROVEEDORES
#   python scripts/probar_preguntas.py --proveedores groq      # solo Groq
#   python scripts/probar_preguntas.py --desde 1 --hasta 5     # una tanda
#   python scripts/probar_preguntas.py --proveedores ollama --ollama-modelo qwen2.5:3b   # local (GTX 1650 Super)
#   python scripts/probar_preguntas.py --proveedores ollama --ollama-modelo qwen2.5:7b   # local (RTX 3060 12 GB)
# Ollama es opcional: se usa solo si ATENCION_OLLAMA_URL (o --ollama-url) apunta a un servidor de Ollama.
import argparse
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
_tmp = tempfile.mkdtemp(prefix="atencion_prueba_")
os.environ["ATENCION_DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'prueba.db'}"
os.environ["ATENCION_DB_SCHEMA"] = ""
os.environ["ATENCION_ENABLED"] = "true"

import httpx  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.ia.fabrica import config_ia, crear_cadena  # noqa: E402
from app.ia.proveedores import timeout_http  # noqa: E402
from app.main import preparar_conocimiento  # noqa: E402
from app.repositories import conversacion_repository  # noqa: E402
from app.services import chat_service  # noqa: E402

PREGUNTAS = RAIZ / "scripts" / "preguntas.txt"


def leer_preguntas() -> list[str]:
    """Preguntas del archivo, una por linea; '#' son comentarios. Sin input."""
    lineas = PREGUNTAS.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lineas if ln.strip() and not ln.strip().startswith("#")]


async def responder(cadena, http, pregunta: str, numero: int) -> tuple[str, str, float]:
    """Hace una pregunta en una conversacion nueva y devuelve (texto, modo, segundos). Recibe cadena, http,
    pregunta y su numero."""
    db = SessionLocal()
    inicio = time.monotonic()
    try:
        conversacion = conversacion_repository.crear(db, f"{numero:032x}", "prueba", "es", "landing")
        texto, modo = "", "?"
        async for evento in chat_service.conversar(db, conversacion, pregunta, "texto", cadena, http):
            if evento["tipo"] == "texto":
                texto += evento["texto"]
            elif evento["tipo"] == "reemplazar":
                texto = evento["texto"]
            elif evento["tipo"] == "fin":
                modo = evento["modo"]
        return texto, modo, time.monotonic() - inicio
    finally:
        db.close()


async def main() -> None:
    """Corre la tanda pedida e imprime pregunta, modo, tiempo y respuesta. Sin input (usa argumentos)."""
    parser = argparse.ArgumentParser(description="Prueba el asistente de atención con IA real, por tandas")
    parser.add_argument("--proveedores", help="lista separada por comas (por defecto, ATENCION_PROVEEDORES)")
    parser.add_argument("--desde", type=int, default=1)
    parser.add_argument("--hasta", type=int, default=0)
    parser.add_argument("--pausa", type=float, default=2.0, help="segundos entre preguntas (cuidar la cuota)")
    parser.add_argument("--ollama-url", help="servidor de Ollama (por defecto ATENCION_OLLAMA_URL; local: http://localhost:11434)")
    parser.add_argument("--ollama-modelo", help="modelo de Ollama, p. ej. qwen2.5:7b o qwen2.5:3b (por defecto ATENCION_OLLAMA_MODELO)")
    args = parser.parse_args()

    extra = {}
    if args.ollama_url:
        extra["ATENCION_OLLAMA_URL"] = args.ollama_url
    if args.ollama_modelo:
        extra["ATENCION_OLLAMA_MODELO"] = args.ollama_modelo
    ajustes = Settings(_env_file=str(RAIZ.parent / ".env"), **extra)
    orden = [p.strip() for p in args.proveedores.split(",")] if args.proveedores else None
    cadena = crear_cadena(ajustes, orden)
    if not cadena.proveedores:
        sys.exit("No hay proveedores con clave para esta tanda (revisa el .env de la raíz).")
    print("Proveedores:", ", ".join(f"{p.nombre} ({p.modelo})" for p in cadena.proveedores))
    preparar_conocimiento()

    preguntas = leer_preguntas()
    hasta = args.hasta or len(preguntas)
    async with httpx.AsyncClient(timeout=timeout_http(config_ia(ajustes))) as http:
        for numero in range(args.desde, hasta + 1):
            pregunta = preguntas[numero - 1]
            texto, modo, seg = await responder(cadena, http, pregunta, numero)
            print(f"\n[{numero}] {pregunta}\n  modo={modo} · {seg:.1f} s\n  {texto.strip()}")
            await asyncio.sleep(args.pausa)


if __name__ == "__main__":
    asyncio.run(main())
