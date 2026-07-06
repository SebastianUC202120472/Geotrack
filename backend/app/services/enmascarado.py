# Enmascarado de datos personales para respuestas del portal ANTES de verificar
# identidad. Logica pura (sin BD).
import re


def mask_telefono(tel: str) -> str:
    """Enmascara un telefono dejando prefijo y ultimos 2 digitos. Recibe el telefono crudo.
    Devuelve el patron '+51 9** *** *21' (o '' si no hay telefono)."""
    if not tel:
        return ""
    digitos = re.sub(r"\D", "", tel)
    ultimos = digitos[-2:] if len(digitos) >= 2 else digitos
    return "+51 9** *** *" + ultimos


def mask_nombre(nombre: str) -> str:
    """Enmascara un nombre dejando las 4 primeras letras + '•••'. Recibe el nombre."""
    if not nombre:
        return ""
    return nombre.strip()[:4] + "•••"


def mask_direccion_corta(direccion: str) -> str:
    """Enmascara una direccion dejando la primera palabra + ' ••• •••'. Recibe la direccion."""
    if not direccion:
        return ""
    return direccion.split(" ")[0] + " ••• •••"


def mask_correo(email: str) -> str:
    """Enmascara un correo: 'ab***@dominio'. Recibe el email."""
    if not email or "@" not in email:
        return ""
    u, d = email.split("@", 1)
    return (u[:2] + "***@" + d)


def mask_direccion(direccion: str) -> str:
    """Enmascara una direccion conservando el distrito tras la coma. Recibe la direccion completa.
    'Av. Larco 812, Miraflores' -> 'Av. L•••• 8••, Miraflores'."""
    if not direccion:
        return ""
    partes = direccion.split(",")
    calle = partes[0].strip()
    resto = ("," + ",".join(partes[1:])) if len(partes) > 1 else ""
    tokens = calle.split(" ")
    enmascarados = []
    for tok in tokens:
        if len(tok) <= 2:
            enmascarados.append(tok)  # 'Av.', numeros cortos: se dejan
        elif tok.isdigit():
            enmascarados.append(tok[0] + "•" * (len(tok) - 1))
        else:
            enmascarados.append(tok[0] + "•" * (len(tok) - 1))
    return " ".join(enmascarados) + resto
