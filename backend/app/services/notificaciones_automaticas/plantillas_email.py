"""Renderizador HTML común para los correos transaccionales de GeoTrack."""
import html
import re


_URL_RE = re.compile(r"(https?://[^\s<]+)")


def _enlaces_seguros(texto: str) -> str:
    """Escapa texto y convierte URLs en enlaces sin permitir HTML arbitrario."""
    escapado = html.escape(texto or "")
    return _URL_RE.sub(
        r'<a href="\1" style="color:#2679d8;text-decoration:none;font-weight:600;">\1</a>',
        escapado,
    )


def renderizar_email(asunto: str, cuerpo: str, evento: str | None = None) -> str:
    """Devuelve un correo HTML compatible con clientes de correo comunes."""
    titulo = html.escape(asunto or "Notificación GeoTrack")
    etiqueta = html.escape((evento or "NOTIFICACIÓN").replace("_", " ").title())
    bloques = []
    for bloque in (cuerpo or "").split("\n\n"):
        contenido = _enlaces_seguros(bloque).replace("\n", "<br>")
        if contenido.strip():
            bloques.append(f'<p style="margin:0 0 16px;color:#334155;line-height:1.65;">{contenido}</p>')
    contenido_html = "".join(bloques) or '<p style="color:#334155;">Sin contenido adicional.</p>'

    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{titulo}</title>
  </head>
  <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;color:#0f2b4a;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{titulo} · GeoTrack</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f1f5f9;">
      <tr>
        <td align="center" style="padding:28px 12px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:620px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 8px 28px rgba(15,43,74,.10);">
            <tr>
              <td style="background:#0f2b4a;padding:24px 32px;">
                <div style="font-size:21px;line-height:1.2;font-weight:700;color:#ffffff;letter-spacing:.2px;">Geo<span style="color:#63b3ed;">Track</span></div>
                <div style="margin-top:7px;color:#cbd5e1;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;">Centro de operaciones</div>
              </td>
            </tr>
            <tr>
              <td style="padding:32px 36px 22px;">
                <div style="display:inline-block;padding:6px 10px;border-radius:999px;background:#eaf4ff;color:#2679d8;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">{etiqueta}</div>
                <h1 style="margin:16px 0 22px;color:#0f2b4a;font-size:25px;line-height:1.25;font-weight:700;">{titulo}</h1>
                <div style="font-size:15px;">{contenido_html}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 36px 30px;">
                <div style="height:1px;background:#e2e8f0;"></div>
                <p style="margin:18px 0 0;color:#64748b;font-size:12px;line-height:1.5;">Este es un mensaje automático de GeoTrack. Si necesitas ayuda, contacta al equipo de operaciones.</p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8fafc;padding:18px 36px;text-align:center;color:#94a3b8;font-size:11px;line-height:1.5;">GeoTrack · Gestión de última milla</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
