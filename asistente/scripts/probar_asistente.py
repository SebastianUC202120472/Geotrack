# Envia preguntas al asistente (/api/asistente/chat) pasando por Nginx, como lo hace el
# widget del panel, y muestra por cada una: la respuesta, los bloques (tablas, graficos y
# enlaces), los pasos de consulta y los errores. Del .env solo lee ADMIN_EMAIL y ADMIN_PASSWORD.
#
# Uso (desde la raiz del repo, con docker compose levantado y ASISTENTE_ENABLED=true):
#   python asistente/scripts/probar_asistente.py                       # usa preguntas.txt
#   python asistente/scripts/probar_asistente.py "¿Cómo va el día?"    # una o varias preguntas sueltas
#   python asistente/scripts/probar_asistente.py --archivo otras.txt --misma-conversacion
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comun import URL_BASE_POR_DEFECTO, ErrorApi, iniciar_sesion, peticion, preparar_consola  # noqa: E402

CARPETA = os.path.dirname(os.path.abspath(__file__))
SEPARADOR = "-" * 72


def leer_preguntas(ruta: str) -> list[str]:
    """Lee una pregunta por linea, ignorando lineas vacias y comentarios (#). Recibe la ruta."""
    if not os.path.isfile(ruta):
        raise SystemExit(f"ERROR: no existe el archivo de preguntas {ruta}")
    with open(ruta, encoding="utf-8-sig") as archivo:
        return [l.strip() for l in archivo if l.strip() and not l.lstrip().startswith("#")]


def _eventos_sse(respuesta):
    """Recorre un flujo Server-Sent Events y entrega cada evento como dict. Recibe la respuesta HTTP."""
    datos = []
    for linea_bytes in respuesta:
        linea = linea_bytes.decode("utf-8").rstrip("\r\n")
        if linea.startswith("data:"):
            datos.append(linea[5:].lstrip())
        elif linea == "" and datos:
            try:
                yield json.loads("\n".join(datos))
            except ValueError:
                yield {"tipo": "error", "codigo": "-", "texto": "Evento ilegible: " + " ".join(datos)[:200]}
            datos = []
    if datos:
        yield json.loads("\n".join(datos))


def mostrar_bloque(bloque: dict) -> None:
    """Imprime un bloque del asistente en texto plano. Recibe el bloque."""
    tipo = bloque.get("tipo")
    if tipo == "tabla":
        filas, total = bloque.get("filas", []), bloque.get("total", 0)
        print(f"  [tabla] {bloque.get('titulo', '')} ({total} fila(s){', se muestran ' + str(len(filas)) if total > len(filas) else ''})")
        print("    " + " | ".join(bloque.get("columnas", [])))
        for fila in filas:
            print("    " + " | ".join("" if v is None else str(v) for v in fila))
    elif tipo == "grafico":
        print(f"  [gráfico {bloque.get('forma', '')}] {bloque.get('titulo', '')}")
        for punto in bloque.get("datos", []):
            print(f"    {punto.get('etiqueta')}: {punto.get('valor')}")
    elif tipo == "enlace":
        print(f"  [enlace] {bloque.get('texto')} -> {bloque.get('ruta')}")
    else:
        print(f"  [{tipo}] {json.dumps(bloque, ensure_ascii=False)[:300]}")


def preguntar(url: str, token: str, mensaje: str, conversacion_id: str | None, timeout: float) -> tuple[str | None, bool]:
    """Envia una pregunta y muestra lo que llega. Recibe url, token, mensaje, conversacion y timeout.
    Devuelve (conversacion_id, hubo_error)."""
    cuerpo = {"mensaje": mensaje}
    if conversacion_id:
        cuerpo["conversacion_id"] = conversacion_id
    req = urllib.request.Request(
        f"{url}/api/asistente/chat",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    inicio = time.monotonic()
    texto, bloques, hubo_error = [], [], False
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for evento in _eventos_sse(resp):
                tipo = evento.get("tipo")
                if tipo == "inicio":
                    conversacion_id = evento.get("conversacion_id") or conversacion_id
                elif tipo == "estado":
                    print(f"  … {evento.get('texto')}")
                elif tipo == "texto":
                    texto.append(evento.get("texto", ""))
                elif tipo == "bloque":
                    bloques.append(evento.get("bloque") or {})
                elif tipo == "error":
                    hubo_error = True
                    print(f"  ! ERROR {evento.get('codigo')}: {evento.get('texto')}")
    except urllib.error.HTTPError as exc:
        try:
            detalle = json.loads(exc.read().decode("utf-8") or "{}").get("detail", exc.reason)
        except (ValueError, UnicodeDecodeError, AttributeError):
            detalle = exc.reason
        print(f"  ! ERROR HTTP {exc.code}: {detalle}")
        return conversacion_id, True
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  ! ERROR de conexión: {getattr(exc, 'reason', exc)}")
        return conversacion_id, True

    respuesta = "".join(texto).strip()
    print("Respuesta:")
    print("  " + (respuesta.replace("\n", "\n  ") if respuesta else "(sin texto)"))
    if bloques:
        print(f"Bloques ({len(bloques)}):")
        for bloque in bloques:
            mostrar_bloque(bloque)
    else:
        print("Bloques: ninguno")
    print(f"Tiempo: {time.monotonic() - inicio:.1f} s")
    return conversacion_id, hubo_error


def main() -> int:
    """Envia las preguntas y resume cuantas fallaron. Devuelve el codigo de salida."""
    preparar_consola()
    parser = argparse.ArgumentParser(description="Prueba el asistente del panel enviando preguntas por Nginx.")
    parser.add_argument("preguntas", nargs="*", help="Preguntas sueltas (si no se dan, se usa --archivo)")
    parser.add_argument("--archivo", default=os.path.join(CARPETA, "preguntas.txt"), help="Una pregunta por línea")
    parser.add_argument("--url", default=URL_BASE_POR_DEFECTO, help="URL de Nginx (por defecto %(default)s)")
    parser.add_argument("--env", default=None, help="Ruta del .env (por defecto el de la raíz del repo)")
    parser.add_argument("--misma-conversacion", action="store_true",
                        help="Envía todas las preguntas en una sola conversación (para probar el contexto)")
    parser.add_argument("--pausa", type=float, default=7.0,
                        help="Segundos entre preguntas, para no chocar con el límite por minuto (por defecto %(default)s)")
    parser.add_argument("--timeout", type=float, default=120.0, help="Segundos máximos por respuesta")
    args = parser.parse_args()
    url = args.url.rstrip("/")

    preguntas = args.preguntas or leer_preguntas(args.archivo)
    if not preguntas:
        raise SystemExit("ERROR: no hay preguntas que enviar.")

    try:
        estado = peticion("GET", f"{url}/api/asistente/estado")
    except ErrorApi as exc:
        raise SystemExit(f"ERROR: el asistente no responde (HTTP {exc.codigo}: {exc.detalle}). "
                         "¿Está levantado el contenedor 'asistente'?")
    if not (estado or {}).get("activo"):
        print("AVISO: el asistente figura INACTIVO (ASISTENTE_ENABLED=false o sin proveedores de IA). Se intenta igual.")

    token = iniciar_sesion(url, args.env)
    conversacion_id, fallidas = None, 0
    for i, pregunta in enumerate(preguntas, 1):
        if i > 1 and args.pausa > 0:
            time.sleep(args.pausa)
        print(SEPARADOR)
        print(f"[{i}/{len(preguntas)}] {pregunta}")
        nueva_id, hubo_error = preguntar(url, token, pregunta, conversacion_id if args.misma_conversacion else None, args.timeout)
        if args.misma_conversacion:
            conversacion_id = nueva_id
        fallidas += int(hubo_error)

    print(SEPARADOR)
    print(f"Resultado: {len(preguntas) - fallidas} de {len(preguntas)} pregunta(s) sin errores.")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
