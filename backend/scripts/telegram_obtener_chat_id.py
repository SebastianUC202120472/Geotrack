"""Imprime los chat_id que hayan iniciado el bot con /start.

Uso dentro del contenedor:
    python scripts/telegram_obtener_chat_id.py
"""
import json
import os
from urllib.request import urlopen


def main() -> None:
    """Muestra los chats que escribieron al bot para copiar su chat_id. Sin input."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    with urlopen(url, timeout=20) as respuesta:  # nosec B310 - URL fija de Telegram
        resultado = json.loads(respuesta.read().decode("utf-8"))
    if not resultado.get("ok"):
        raise SystemExit(f"Telegram rechazo la consulta: {resultado}")
    encontrados = set()
    for actualizacion in resultado.get("result", []):
        mensaje = actualizacion.get("message") or actualizacion.get("edited_message") or {}
        chat = mensaje.get("chat") or {}
        if chat.get("id") is not None:
            clave = (chat["id"], chat.get("type"), chat.get("username"), chat.get("first_name"))
            encontrados.add(clave)
    if not encontrados:
        print("No hay chats. Envia /start al bot y ejecuta el script nuevamente.")
        return
    for chat_id, tipo, username, nombre in sorted(encontrados, key=lambda item: str(item[0])):
        print(f"chat_id={chat_id} tipo={tipo or ''} username={username or ''} nombre={nombre or ''}")


if __name__ == "__main__":
    main()
