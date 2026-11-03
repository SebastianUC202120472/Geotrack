# Utilidades para exportar a Excel datos que escriben terceros (formularios publicos, Excel de clientes).


def celda_segura(valor):
    """Evita la inyeccion de formulas: un texto que empieza con =, +, -, @, tabulador o retorno se
    guarda como texto anteponiendo un apostrofo. Recibe el valor de la celda."""
    if isinstance(valor, str) and valor[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + valor
    return valor


def fila_segura(valores) -> list:
    """Aplica celda_segura a todos los valores de una fila. Recibe un iterable de valores."""
    return [celda_segura(v) for v in valores]
