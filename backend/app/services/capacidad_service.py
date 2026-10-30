# Logica del modulo de catalogo y capacidad (Idea 3).
# No conoce HTTP: recibe datos, consulta el repositorio y devuelve diccionarios
# que el router convierte a los esquemas Pydantic.
import json
import math
import time
from collections import defaultdict
import os
import re
import unicodedata
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.ruta import Ruta

from app.models.capacidad import (
    ConfiguracionCapacidad,
    ModeloPersonalizado,
    VinculacionPlaca,
)
from app.repositories import capacidad_repository, usuario_repository, vehiculo_repository
from app.schemas.capacidad import (
    CalculoRequest,
    CatalogoEstructuraJSON,
    ConfiguracionUpdateRequest,
    FiltrosPedidos,
    ModeloCreateRequest,
    ModeloUpdateRequest,
    ModeloVehiculo,
    VinculacionPlacaRequest,
    validar_fuente_tecnica,
)

# Tope duro de pedidos por calculo: evita que una peticion congele el servidor.
MAX_PEDIDOS = 5000

# Medidas de referencia cuando el pedido no trae peso o volumen.
# Se marcan siempre como "estimado" en la respuesta.
TAMANOS_ESTANDAR = {
    "S": {"peso_kg": 5.0, "volumen_m3": 0.03, "etiqueta": "S (pequeno)"},
    "M": {"peso_kg": 15.0, "volumen_m3": 0.09, "etiqueta": "M (mediano)"},
    "L": {"peso_kg": 40.0, "volumen_m3": 0.25, "etiqueta": "L (grande)"},
}

CAMPOS_MODELO = (
    "marca",
    "modelo",
    "tipo",
    "largo_m",
    "ancho_m",
    "alto_m",
    "volumen_util_m3",
    "carga_util_kg",
    "fuente",
    "fuente_url",
    "verificado",
)

RUTA_CATALOGO = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "api",
    "modulo_capacidad",
    "catalogo_vehiculos.json",
)


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def leer_catalogo_base() -> CatalogoEstructuraJSON:
    """Lee y valida el JSON base del catalogo una sola vez. Sin parametros."""
    if not os.path.exists(RUTA_CATALOGO):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No existe el catalogo base de vehiculos.",
        )
    with open(RUTA_CATALOGO, "r", encoding="utf-8") as archivo:
        contenido = json.load(archivo)
    catalogo = CatalogoEstructuraJSON(**contenido)
    ids = [modelo.id for modelo in catalogo.modelos]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=500, detail="El JSON contiene modelos duplicados.")
    return catalogo


def _slug(texto: str) -> str:
    """Convierte texto en un id seguro (minusculas con guiones). Recibe el texto."""
    normalizado = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", normalizado.lower()).strip("-")


def _modelo_desde_fila(fila: ModeloPersonalizado) -> dict:
    """Arma el diccionario de un modelo guardado en la base. Recibe la fila."""
    return {
        "id": fila.modelo_id,
        "marca": fila.marca,
        "modelo": fila.modelo,
        "tipo": fila.tipo,
        "largo_m": fila.largo_m,
        "ancho_m": fila.ancho_m,
        "alto_m": fila.alto_m,
        "volumen_util_m3": fila.volumen_util_m3,
        "carga_util_kg": fila.carga_util_kg,
        "fuente": fila.fuente,
        "fuente_url": fila.fuente_url,
        "verificado": fila.verificado,
        "es_personalizado": True,
    }


def catalogo_completo(db: Session) -> List[ModeloVehiculo]:
    """Mezcla el JSON base con las altas y ediciones del panel. Recibe la sesion."""
    combinado: Dict[str, dict] = {}

    for modelo in leer_catalogo_base().modelos:
        datos = modelo.model_dump()
        datos["es_personalizado"] = False
        combinado[modelo.id] = datos

    for fila in capacidad_repository.listar_modelos_personalizados(db):
        datos = _modelo_desde_fila(fila)
        if fila.es_nuevo or fila.modelo_id not in combinado:
            combinado[fila.modelo_id] = datos
        else:
            # Una edicion pisa solo los campos guardados; conserva el resto.
            combinado[fila.modelo_id] = {**combinado[fila.modelo_id], **datos}
            combinado[fila.modelo_id]["es_personalizado"] = True

    return [
        ModeloVehiculo(**datos)
        for datos in sorted(combinado.values(), key=lambda d: (d["marca"], d["modelo"]))
    ]


def _sin_acentos(texto: str) -> str:
    """Quita acentos y pasa a minusculas para comparar. Recibe el texto."""
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def filtrar_catalogo(
    modelos: List[ModeloVehiculo],
    busqueda: Optional[str] = None,
    marca: Optional[str] = None,
    tipo: Optional[str] = None,
    solo_verificados: bool = False,
) -> List[ModeloVehiculo]:
    """Filtra el catalogo ya cargado. Recibe busqueda, marca, tipo y bandera."""
    resultado = modelos

    if busqueda:
        texto = _sin_acentos(busqueda.strip())
        resultado = [
            m
            for m in resultado
            if texto in _sin_acentos(f"{m.marca} {m.modelo} {m.id}")
        ]
    if marca:
        objetivo = _sin_acentos(marca.strip())
        resultado = [m for m in resultado if _sin_acentos(m.marca) == objetivo]
    if tipo:
        resultado = [m for m in resultado if m.tipo.value == tipo]
    if solo_verificados:
        resultado = [m for m in resultado if m.verificado]

    return resultado


def obtener_modelo(db: Session, modelo_id: str) -> Optional[ModeloVehiculo]:
    """Busca un modelo (base o propio) por id. Recibe la sesion y el id."""
    for modelo in catalogo_completo(db):
        if modelo.id == modelo_id:
            return modelo
    return None


def crear_modelo(db: Session, datos: ModeloCreateRequest, usuario: str) -> ModeloVehiculo:
    """Agrega un modelo nuevo al catalogo. Recibe la sesion, los datos y el usuario."""
    modelo_id = datos.id or _slug(f"{datos.marca} {datos.modelo}")

    if obtener_modelo(db, modelo_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un modelo con el id '{modelo_id}'.",
        )

    modelo = ModeloVehiculo(**datos.model_dump(exclude={"id"}), id=modelo_id)

    fila = ModeloPersonalizado(
        modelo_id=modelo.id,
        es_nuevo=True,
        marca=modelo.marca,
        modelo=modelo.modelo,
        tipo=modelo.tipo.value,
        largo_m=modelo.largo_m,
        ancho_m=modelo.ancho_m,
        alto_m=modelo.alto_m,
        volumen_util_m3=modelo.volumen_util_m3,
        carga_util_kg=modelo.carga_util_kg,
        fuente=modelo.fuente,
        fuente_url=modelo.fuente_url,
        verificado=modelo.verificado,
        creado_por=usuario,
    )
    capacidad_repository.guardar_modelo_personalizado(db, fila)
    capacidad_repository.registrar_auditoria(
        db, "crear", "modelo", modelo.id, f"{modelo.marca} {modelo.modelo}", usuario
    )
    db.commit()
    return obtener_modelo(db, modelo.id)


def actualizar_modelo(
    db: Session, modelo_id: str, datos: ModeloUpdateRequest, usuario: str
) -> ModeloVehiculo:
    """Edita un modelo; si es del JSON base guarda una copia. Recibe id y cambios."""
    actual = obtener_modelo(db, modelo_id)
    if actual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El modelo no existe en el catalogo.",
        )

    fusionado = actual.model_dump()
    fusionado.update(datos.model_dump(exclude_unset=True))
    validado = ModeloVehiculo(**fusionado)
    try:
        validar_fuente_tecnica(validado.fuente, validado.fuente_url)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    fila = capacidad_repository.obtener_modelo_personalizado(db, modelo_id)
    if fila is None:
        fila = ModeloPersonalizado(
            modelo_id=modelo_id,
            es_nuevo=False,
            creado_por=usuario,
        )

    for campo in CAMPOS_MODELO:
        valor = getattr(validado, campo)
        if campo == "tipo":
            valor = valor.value
        setattr(fila, campo, valor)

    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    capacidad_repository.guardar_modelo_personalizado(db, fila)
    capacidad_repository.registrar_auditoria(
        db,
        "editar",
        "modelo",
        modelo_id,
        ", ".join(datos.model_dump(exclude_unset=True).keys()),
        usuario,
    )
    db.commit()
    return obtener_modelo(db, modelo_id)


def eliminar_modelo(db: Session, modelo_id: str, usuario: str) -> None:
    """Borra un modelo agregado desde el panel. Los del JSON base no se borran."""
    if obtener_modelo(db, modelo_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El modelo no existe en el catalogo.",
        )

    fila = capacidad_repository.obtener_modelo_personalizado(db, modelo_id)
    if fila is None or not fila.es_nuevo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Los modelos del catalogo base no se eliminan; puedes editarlos.",
        )

    vinculadas = [
        v for v in capacidad_repository.listar_vinculaciones(db) if v.modelo_id == modelo_id
    ]
    if vinculadas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El modelo esta vinculado a una placa de la flota.",
        )

    capacidad_repository.eliminar_modelo_personalizado(db, fila)
    capacidad_repository.registrar_auditoria(
        db, "eliminar", "modelo", modelo_id, None, usuario
    )
    db.commit()


# ---------------------------------------------------------------------------
# Vinculaciones con la flota
# ---------------------------------------------------------------------------


def configuracion_dict(config: ConfiguracionCapacidad) -> dict:
    """Expone configuracion y medidas S/M/L guardadas por el modulo."""
    return {
        "factor_aprovechamiento": config.factor_aprovechamiento,
        "max_paradas_por_viaje": config.max_paradas_por_viaje,
        "max_paradas_por_jornada": config.max_paradas_por_jornada,
        "max_viajes_por_dia": config.max_viajes_por_dia,
        "s_peso_kg": config.s_peso_kg,
        "s_volumen_m3": config.s_volumen_m3,
        "m_peso_kg": config.m_peso_kg,
        "m_volumen_m3": config.m_volumen_m3,
        "l_peso_kg": config.l_peso_kg,
        "l_volumen_m3": config.l_volumen_m3,
        "actualizado_por": config.actualizado_por,
        "actualizado_en": config.actualizado_en,
    }


def tamanos_desde_config(config: ConfiguracionCapacidad) -> dict:
    """Obtiene la tabla de medidas estandar para calculos reales y demo."""
    return {
        "S": {"peso_kg": config.s_peso_kg, "volumen_m3": config.s_volumen_m3},
        "M": {"peso_kg": config.m_peso_kg, "volumen_m3": config.m_volumen_m3},
        "L": {"peso_kg": config.l_peso_kg, "volumen_m3": config.l_volumen_m3},
    }


def obtener_configuracion(db: Session) -> ConfiguracionCapacidad:
    """Devuelve la configuracion y crea la fila por defecto si falta. Recibe la sesion."""
    config = capacidad_repository.obtener_configuracion(db)
    if config is not None:
        return config

    config = ConfiguracionCapacidad(
        id=1,
        factor_aprovechamiento=0.85,
        max_paradas_por_viaje=25,
        max_paradas_por_jornada=60,
        max_viajes_por_dia=3,
    )
    capacidad_repository.guardar_configuracion(db, config)
    try:
        db.commit()
    except Exception:
        # Otro proceso pudo crearla al mismo tiempo: se relee.
        db.rollback()
        config = capacidad_repository.obtener_configuracion(db)
        if config is None:
            raise
        return config
    db.refresh(config)
    return config


def actualizar_configuracion(
    db: Session, datos: ConfiguracionUpdateRequest, usuario: str
) -> ConfiguracionCapacidad:
    """Cambia los parametros de planificacion. Recibe datos y usuario."""
    config = obtener_configuracion(db)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(config, campo, valor)
    config.actualizado_por = usuario
    config.actualizado_en = datetime.utcnow()
    capacidad_repository.guardar_configuracion(db, config)
    capacidad_repository.registrar_auditoria(
        db,
        "editar",
        "configuracion",
        str(config.id),
        ", ".join(datos.model_dump(exclude_unset=True).keys()),
        usuario,
    )
    db.commit()
    db.refresh(config)
    return config


def _respuesta_vinculacion(fila, modelo, vehiculo) -> dict:
    """Arma la respuesta de una vinculacion con datos del vehiculo. Recibe las filas."""
    return {
        "id": fila.id,
        "placa": fila.placa,
        "modelo_id": fila.modelo_id,
        "modelo": modelo.model_dump() if modelo else None,
        "marca": modelo.marca if modelo else None,
        "nombre_modelo": modelo.modelo if modelo else None,
        "tipo": modelo.tipo.value if modelo else None,
        "capacidad_m3": modelo.volumen_util_m3 if modelo else None,
        "carga_kg": modelo.carga_util_kg if modelo else None,
        "creado_por": fila.creado_por,
        "creado_en": fila.creado_en,
        "vehiculo_encontrado": vehiculo is not None,
        "conductor": None,
    }


def respuesta_vinculacion(db: Session, fila: VinculacionPlaca) -> dict:
    """Arma la respuesta completa de una vinculacion. Recibe la fila guardada."""
    modelo = obtener_modelo(db, fila.modelo_id)
    vehiculo = vehiculo_repository.obtener_por_placa(db, fila.placa)
    datos = _respuesta_vinculacion(fila, modelo, vehiculo)
    datos["conductor"] = _nombre_conductor(db, vehiculo) if vehiculo else None
    return datos


def _nombre_conductor(db: Session, vehiculo) -> Optional[str]:
    """Devuelve el nombre del conductor del vehiculo, si tiene. Recibe la sesion."""
    conductor_id = getattr(vehiculo, "conductor_id", None)
    if not conductor_id:
        return None
    conductor = usuario_repository.obtener_por_id(db, conductor_id)
    if conductor is None:
        return None
    return getattr(conductor, "nombre", None) or getattr(conductor, "correo", None)


def vincular(
    db: Session, datos: VinculacionPlacaRequest, usuario: str
) -> VinculacionPlaca:
    """Vincula una placa existente de la flota con un modelo. Recibe los datos."""
    modelo = obtener_modelo(db, datos.modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El modelo no existe en el catalogo.",
        )

    vehiculo = vehiculo_repository.obtener_por_placa(db, datos.placa)
    if vehiculo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La placa no existe en la flota. Registrala primero en Flota.",
        )
    if getattr(vehiculo, "eliminado_en", None) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La placa pertenece a un vehiculo dado de baja.",
        )

    if capacidad_repository.obtener_vinculacion_por_placa(db, datos.placa):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esa placa ya tiene un modelo vinculado.",
        )

    fila = VinculacionPlaca(
        placa=datos.placa,
        modelo_id=modelo.id,
        creado_por=usuario,
    )
    capacidad_repository.crear_vinculacion(db, fila)
    capacidad_repository.registrar_auditoria(
        db, "vincular", "placa", datos.placa, modelo.id, usuario
    )
    db.commit()
    db.refresh(fila)
    return fila


def listar_vinculaciones(db: Session) -> List[dict]:
    """Lista las vinculaciones con datos del vehiculo y del modelo. Recibe la sesion."""
    catalogo = {m.id: m for m in catalogo_completo(db)}
    vehiculos = {v.placa: v for v in vehiculo_repository.listar(db)}

    salida = []
    for fila in capacidad_repository.listar_vinculaciones(db):
        vehiculo = vehiculos.get(fila.placa)
        respuesta = _respuesta_vinculacion(
            fila, catalogo.get(fila.modelo_id), vehiculo
        )
        respuesta["conductor"] = _nombre_conductor(db, vehiculo) if vehiculo else None
        salida.append(respuesta)
    return salida


def eliminar_vinculacion(db: Session, vinculacion_id: int, usuario: str) -> None:
    """Quita la vinculacion de una placa. Recibe la sesion, el id y el usuario."""
    fila = capacidad_repository.obtener_vinculacion(db, vinculacion_id)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La vinculacion no existe.",
        )
    placa = fila.placa
    capacidad_repository.eliminar_vinculacion(db, fila)
    capacidad_repository.registrar_auditoria(
        db, "desvincular", "placa", placa, None, usuario
    )
    db.commit()


def listar_flota(db: Session) -> List[dict]:
    """Lista la flota con su vinculacion (si tiene). Recibe la sesion."""
    catalogo = {m.id: m for m in catalogo_completo(db)}
    vinculaciones = {
        v.placa: v for v in capacidad_repository.listar_vinculaciones(db)
    }

    salida = []
    for vehiculo in vehiculo_repository.listar(db):
        fila = vinculaciones.get(vehiculo.placa)
        vinculacion = None
        if fila is not None:
            vinculacion = _respuesta_vinculacion(
                fila, catalogo.get(fila.modelo_id), vehiculo
            )
            vinculacion["conductor"] = _nombre_conductor(db, vehiculo)
        salida.append(
            {
                "id": vehiculo.id,
                "placa": vehiculo.placa,
                "marca": vehiculo.marca,
                "capacidad_volumetrica": vehiculo.capacidad_volumetrica,
                "capacidad_cajas": vehiculo.capacidad_cajas,
                "estado": vehiculo.estado,
                "conductor": _nombre_conductor(db, vehiculo),
                "vinculacion": vinculacion,
            }
        )
    return salida


# ---------------------------------------------------------------------------
# Calculadora y planificacion
# ---------------------------------------------------------------------------


def _tamano_estimado(pedido_id: int) -> str:
    """Asigna un tamano S/M/L estable a un pedido sin medidas. Recibe el id."""
    # Distribucion 50% S, 33% M, 17% L: se mantiene igual entre llamadas.
    return ("S", "S", "S", "M", "M", "L")[int(pedido_id) % 6]


def items_desde_pedidos(pedidos, tamanos: Optional[dict] = None) -> List[dict]:
    """Lee peso y volumen reales; faltantes se estiman con M configurable."""
    tamanos = tamanos or TAMANOS_ESTANDAR
    items = []
    for pedido in pedidos:
        peso = getattr(pedido, "peso_kg", None)
        volumen = getattr(pedido, "volumen_m3", None)
        falta_peso = peso is None or float(peso) <= 0
        falta_volumen = volumen is None or float(volumen) <= 0
        estimado = falta_peso or falta_volumen
        tamano = "M" if estimado else None
        if falta_peso:
            peso = tamanos["M"]["peso_kg"]
        if falta_volumen:
            volumen = tamanos["M"]["volumen_m3"]
        items.append({
            "pedido_id": pedido.id,
            "codigo": pedido.codigo,
            "distrito": pedido.distrito,
            "latitud": getattr(pedido, "latitud", None),
            "longitud": getattr(pedido, "longitud", None),
            "peso_kg": round(float(peso), 3),
            "volumen_m3": round(float(volumen), 4),
            "estimado": estimado,
            "tamano_estimado": tamano,
        })
    return items


def items_desde_cantidades(cantidades: Dict[str, int], tamanos: Optional[dict] = None) -> List[dict]:
    """Convierte la cantidad de cajas en una lista de carga valida."""
    tamanos = tamanos or TAMANOS_ESTANDAR
    if sum(cantidades.values()) > MAX_PEDIDOS:
        raise HTTPException(status_code=400, detail="El maximo es de 5000 cajas.")
    items = []
    for tamano in ("S", "M", "L"):
        estandar = tamanos[tamano]
        for indice in range(int(cantidades.get(tamano, 0))):
            items.append({
                "pedido_id": None,
                "codigo": f"Caja {tamano}-{indice + 1}",
                "distrito": None,
                "peso_kg": estandar["peso_kg"],
                "volumen_m3": estandar["volumen_m3"],
                "estimado": True,
                "tamano_estimado": tamano,
            })
    return items


def items_demo(cantidad: int, tamanos: Optional[dict] = None) -> List[dict]:
    """Genera pedidos sinteticos reproducibles, sin datos personales."""
    if not 1 <= cantidad <= MAX_PEDIDOS:
        raise HTTPException(status_code=400, detail="Indica entre 1 y 5000 pedidos.")
    tamanos = tamanos or TAMANOS_ESTANDAR
    items = []
    for indice in range(1, cantidad + 1):
        tamano = ("S", "S", "S", "M", "M", "L")[indice % 6]
        estandar = tamanos[tamano]
        items.append({
            "pedido_id": None,
            "codigo": f"DEMO-{indice:04d}",
            "distrito": f"Zona {(indice % 8) + 1}",
            "peso_kg": estandar["peso_kg"],
            "volumen_m3": estandar["volumen_m3"],
            "estimado": True,
            "tamano_estimado": tamano,
        })
    return items


def vehiculo_desde_modelo(modelo: ModeloVehiculo, placa: str = "CATALOGO") -> dict:
    """Arma un vehiculo planificable desde un modelo. Recibe modelo y placa."""
    return {
        "placa": placa,
        "modelo_id": modelo.id,
        "marca": modelo.marca,
        "modelo": modelo.modelo,
        "tipo": modelo.tipo.value,
        "volumen_m3": modelo.volumen_util_m3,
        "carga_kg": modelo.carga_util_kg,
    }


def _flota_planificable(db: Session) -> Tuple[List[dict], int, int]:
    """Devuelve flota libre con conductor habilitado y modelo vinculado."""
    catalogo = {m.id: m for m in catalogo_completo(db)}
    vinculaciones = {
        v.placa: v.modelo_id
        for v in capacidad_repository.listar_vinculaciones(db)
    }
    rutas_activas = db.query(Ruta).filter(
        Ruta.estado.in_(("CREADA", "EN_PROGRESO"))
    ).all()
    placas_ocupadas = {r.vehiculo_placa for r in rutas_activas if r.vehiculo_placa}
    conductores_ocupados = {r.conductor_id for r in rutas_activas if r.conductor_id}
    disponibles = []
    sin_modelo = 0
    no_disponibles = 0
    for vehiculo in vehiculo_repository.listar(db):
        modelo = catalogo.get(vinculaciones.get(vehiculo.placa))
        if modelo is None:
            sin_modelo += 1
            continue
        conductor_id = vehiculo.conductor_id
        if vehiculo.estado != "DISPONIBLE" or conductor_id is None:
            no_disponibles += 1
            continue
        conductor = usuario_repository.obtener_por_id(db, conductor_id)
        if not conductor or not conductor.estado or conductor.rol != "conductor":
            no_disponibles += 1
            continue
        if vehiculo.placa in placas_ocupadas or conductor_id in conductores_ocupados:
            no_disponibles += 1
            continue
        disponibles.append(vehiculo_desde_modelo(modelo, vehiculo.placa))
    return disponibles, sin_modelo, no_disponibles


def _vehiculos_demo(cantidad: int, existentes: List[dict]) -> List[dict]:
    """Completa la flota con camiones sinteticos para la demo. Recibe la cantidad."""
    salida = list(existentes[:cantidad])
    while len(salida) < cantidad:
        numero = len(salida) + 1
        salida.append(
            {
                "placa": f"DEMO-{numero:02d}",
                "modelo_id": "demo-camion-ligero",
                "marca": "Demo",
                "modelo": "Camion ligero 7.5 m3",
                "tipo": "camion_ligero",
                "volumen_m3": 7.5,
                "carga_kg": 2000.0,
            }
        )
    return salida


def calcular_plan(
    items: List[dict],
    vehiculos: List[dict],
    factor_aprovechamiento: float,
    max_paradas_por_viaje: int,
    max_viajes_por_dia: int,
    max_paradas_por_jornada: int = 60,
    max_segundos: float = 8.0,
) -> dict:
    """Recomienda viajes por distrito y cercania sin escribir rutas.

    Agrupa por distrito y celda geografica para priorizar destinos cercanos.
    Un mismo viaje puede incluir VARIAS celdas del mismo distrito si aun
    existe capacidad; evita desperdiciar viajes con un solo pedido por celda.

    La cercania es aproximada: NO optimiza distancias de calles ni tiempos.
    Conserva los limites de peso, volumen, paradas, viajes y jornada.
    """
    inicio = time.monotonic()
    if len(items) > MAX_PEDIDOS:
        raise HTTPException(status_code=400, detail="Maximo 5000 pedidos por calculo.")
    if not (0.5 <= factor_aprovechamiento <= 1.0):
        raise HTTPException(status_code=422, detail="Factor invalido.")
    if min(max_paradas_por_viaje, max_paradas_por_jornada, max_viajes_por_dia) < 1:
        raise HTTPException(status_code=422, detail="Los limites deben ser positivos.")

    def comprobar_tiempo():
        if time.monotonic() - inicio > max_segundos:
            raise HTTPException(
                status_code=503,
                detail="Planificacion excede el tiempo maximo permitido.",
            )

    def zona(item):
        distrito = str(item.get("distrito") or "SIN DISTRITO").strip().upper()
        lat, lon = item.get("latitud"), item.get("longitud")
        # Agrupacion aproximada; tolera coordenadas ausentes o invalidas.
        try:
            lat, lon = float(lat), float(lon)
            if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
                return distrito, round(lat, 2), round(lon, 2)
        except (TypeError, ValueError):
            pass
        return distrito, None, None

    grupos = defaultdict(list)
    for item in items:
        peso_item = float(item["peso_kg"])
        volumen_item = float(item["volumen_m3"])
        if (
            not math.isfinite(peso_item) or not math.isfinite(volumen_item)
            or peso_item <= 0 or volumen_item <= 0
        ):
            raise HTTPException(status_code=422, detail="Pedidos con peso o volumen no positivo.")
        grupos[zona(item)].append(item)

    # Orden estable para que dos ejecuciones con los mismos datos sean comparables.
    for grupo in grupos.values():
        grupo.sort(
            key=lambda item: (float(item["volumen_m3"]), float(item["peso_kg"])),
            reverse=True,
        )

    total = len(items)
    peso_total = round(sum(float(i["peso_kg"]) for i in items), 2)
    volumen_total = round(sum(float(i["volumen_m3"]) for i in items), 3)
    estimados = sum(bool(i.get("estimado")) for i in items)
    viajes = []
    alertas = []
    agregados = {
        v["placa"]: {
            "placa": v["placa"], "modelo_id": v["modelo_id"],
            "marca": v.get("marca"), "modelo": v.get("modelo"),
            "viajes": 0, "pedidos": 0, "peso_kg": 0.0,
            "volumen_m3": 0.0, "paradas": 0, "capacidad_total": 0.0,
        }
        for v in vehiculos
    }
    if not vehiculos:
        alertas.append({
            "nivel": "danger", "codigo": "sin_vehiculos",
            "mensaje": f"No hay vehiculos disponibles: {total} pedidos sin asignar.",
        })
        return _armar_respuesta(
            viajes, agregados, alertas, total, estimados, total,
            peso_total, volumen_total, 0, 0.0, 0, vehiculos,
        )

    def prioridad_zona(z):
        return (-len(grupos[z]), z[0], str(z[1:]))

    def cercania(zona_origen, zona_vecina):
        # Primero celdas con coordenadas; despues las que no tienen ubicacion.
        # Solo se compara dentro del MISMO distrito.
        lat1, lon1 = zona_origen[1:]
        lat2, lon2 = zona_vecina[1:]
        if None in (lat1, lon1, lat2, lon2):
            return (1, 0.0, -len(grupos[zona_vecina]), str(zona_vecina))
        # Distancia aproximada cuadratica, sin necesidad de calculo vial.
        distancia = (lat1 - lat2) ** 2 + ((lon1 - lon2) * math.cos(math.radians(lat1))) ** 2
        return (0, distancia, -len(grupos[zona_vecina]), str(zona_vecina))

    for vehiculo in vehiculos:
        comprobar_tiempo()
        placa = vehiculo["placa"]
        carga_max = float(vehiculo["carga_kg"]) * factor_aprovechamiento
        volumen_max = float(vehiculo["volumen_m3"]) * factor_aprovechamiento
        if carga_max <= 0 or volumen_max <= 0:
            alertas.append({
                "nivel": "warning", "codigo": "vehiculo_sin_capacidad",
                "mensaje": f"El vehiculo {placa} no tiene capacidad valida.",
            })
            continue

        agregado = agregados[placa]
        for _ in range(max_viajes_por_dia):
            comprobar_tiempo()
            cupo_paradas = min(
                max_paradas_por_viaje,
                max_paradas_por_jornada - agregado["paradas"],
            )
            if cupo_paradas <= 0:
                break

            # Elegimos una celda inicial que tenga algun pedido que quepa.
            # Se prioriza la celda mas poblada; si un bulto no cabe, se
            # busca otra celda compatible antes de descartar el viaje.
            inicio_zona = None
            for z in sorted(grupos, key=prioridad_zona):
                comprobar_tiempo()
                if any(
                    float(item["peso_kg"]) <= carga_max + 1e-9
                    and float(item["volumen_m3"]) <= volumen_max + 1e-9
                    for item in grupos[z]
                ):
                    inicio_zona = z
                    break
            if inicio_zona is None:
                break

            distrito = inicio_zona[0]
            # CAMBIO PRINCIPAL: completar el viaje con TODAS las celdas
            # cercanas del mismo distrito, no detenerse tras la primera.
            vecinas = sorted(
                (z for z in grupos if z != inicio_zona and z[0] == distrito and grupos[z]),
                key=lambda z: cercania(inicio_zona, z),
            )
            zonas_del_viaje = [inicio_zona, *vecinas]

            seleccionados = []
            peso = 0.0
            volumen = 0.0
            for z in zonas_del_viaje:
                comprobar_tiempo()
                restantes = []
                for item in grupos[z]:
                    item_peso = float(item["peso_kg"])
                    item_volumen = float(item["volumen_m3"])
                    if (
                        len(seleccionados) < cupo_paradas
                        and peso + item_peso <= carga_max + 1e-9
                        and volumen + item_volumen <= volumen_max + 1e-9
                    ):
                        seleccionados.append(item)
                        peso += item_peso
                        volumen += item_volumen
                    else:
                        restantes.append(item)
                grupos[z] = restantes
                if len(seleccionados) >= cupo_paradas:
                    break

            if not seleccionados:
                break

            viajes.append({
                "numero": len(viajes) + 1,
                "vehiculo_placa": placa,
                "modelo_id": vehiculo["modelo_id"],
                "marca": vehiculo.get("marca"),
                "modelo": vehiculo.get("modelo"),
                "pedidos": [
                    {clave: valor for clave, valor in item.items()
                     if clave not in ("latitud", "longitud")}
                    for item in seleccionados
                ],
                "paradas": len(seleccionados),
                "peso_kg": round(peso, 2),
                "volumen_m3": round(volumen, 3),
                "utilizacion_pct": round(volumen / volumen_max * 100, 1),
                "utilizacion_peso_pct": round(peso / carga_max * 100, 1),
                "capacidad_m3": round(volumen_max, 3),
                "capacidad_kg": round(carga_max, 2),
            })
            agregado["viajes"] += 1
            agregado["pedidos"] += len(seleccionados)
            agregado["peso_kg"] = round(agregado["peso_kg"] + peso, 2)
            agregado["volumen_m3"] = round(agregado["volumen_m3"] + volumen, 3)
            agregado["paradas"] += len(seleccionados)
            agregado["capacidad_total"] = round(agregado["capacidad_total"] + volumen_max, 3)

    sin_asignar = sum(len(grupo) for grupo in grupos.values())
    if sin_asignar:
        alertas.append({
            "nivel": "danger", "codigo": "capacidad_insuficiente",
            "mensaje": (
                f"{sin_asignar} pedidos quedaron sin asignar. "
                "La flota o sus limites operativos (peso, volumen, "
                "paradas o viajes) no alcanzaron para planificar todo."
            ),
        })
    if estimados:
        alertas.append({
            "nivel": "warning", "codigo": "datos_estimados",
            "mensaje": f"{estimados} pedidos emplean tamanos referenciales configurables.",
        })
    utilizaciones = [v["utilizacion_pct"] for v in viajes]
    promedio = round(sum(utilizaciones) / len(utilizaciones), 1) if utilizaciones else 0.0
    usados = len({v["vehiculo_placa"] for v in viajes})
    maxima = max((v["paradas"] for v in viajes), default=0)
    return _armar_respuesta(
        viajes, agregados, alertas, total, estimados, sin_asignar,
        peso_total, volumen_total, usados, promedio, maxima, vehiculos,
    )


def _armar_respuesta(
    viajes: List[dict],
    agregados: dict,
    alertas: List[dict],
    total_pedidos: int,
    estimados: int,
    sin_asignar: int,
    peso_total: float,
    volumen_total: float,
    vehiculos_usados: int,
    promedio: float,
    max_paradas: int,
    vehiculos: Optional[List[dict]] = None,
) -> dict:
    """Arma los indicadores y calcula necesidades estimadas sin inventar flota."""
    lista_vehiculos = []
    for agregado in agregados.values():
        utilizacion = (
            agregado["volumen_m3"] / agregado["capacidad_total"] * 100
            if agregado["capacidad_total"] else 0
        )
        lista_vehiculos.append({
            "placa": agregado["placa"], "modelo_id": agregado["modelo_id"],
            "marca": agregado["marca"], "modelo": agregado["modelo"],
            "viajes": agregado["viajes"], "pedidos": agregado["pedidos"],
            "peso_kg": agregado["peso_kg"], "volumen_m3": agregado["volumen_m3"],
            "utilizacion_pct": round(utilizacion, 1), "paradas": agregado["paradas"],
        })
    necesarios = None
    adicionales = None
    if sin_asignar == 0:
        necesarios = vehiculos_usados
        adicionales = 0
    elif vehiculos_usados > 0:
        # Estimacion por productividad observada, NO una asignacion prometida.
        atendidos = total_pedidos - sin_asignar
        promedio_atendidos = atendidos / vehiculos_usados
        if promedio_atendidos > 0:
            adicionales = math.ceil(sin_asignar / promedio_atendidos)
            necesarios = vehiculos_usados + adicionales
    return {
        "resumen": {
            "total_pedidos": total_pedidos,
            "pedidos_estimados": estimados,
            "peso_total_kg": peso_total,
            "volumen_total_m3": volumen_total,
            "viajes_necesarios": len(viajes),
            "vehiculos_disponibles": len(vehiculos or []),
            "vehiculos_usados": vehiculos_usados,
            "vehiculos_necesarios": necesarios,
            "vehiculos_adicionales_estimados": adicionales,
            "utilizacion_promedio_pct": promedio,
            "paradas_maximas_por_viaje": max_paradas,
            "pedidos_sin_asignar": sin_asignar,
        },
        "vehiculos": lista_vehiculos,
        "viajes": viajes,
        "alertas": alertas,
    }


def _resolver_items(db: Session, datos: CalculoRequest, tamanos: Optional[dict] = None) -> Tuple[List[dict], str]:
    """Resuelve un unico origen de pedidos mediante consulta de solo lectura."""
    if datos.cantidades is not None:
        items, modo = items_desde_cantidades(datos.cantidades, tamanos), "cajas"
    elif datos.demo_pedidos is not None:
        items, modo = items_demo(datos.demo_pedidos, tamanos), "demo"
    else:
        filtros = datos.filtros or FiltrosPedidos()
        pedidos = capacidad_repository.listar_pedidos_planificables(
            db, pedido_ids=datos.pedido_ids, estado=filtros.estado,
            distrito=filtros.distrito, fecha=filtros.fecha,
            limite=min(filtros.limite or MAX_PEDIDOS, MAX_PEDIDOS),
        )
        items, modo = items_desde_pedidos(pedidos, tamanos), "pedidos"
    if len(items) > MAX_PEDIDOS:
        raise HTTPException(status_code=400, detail=f"Maximo {MAX_PEDIDOS} pedidos.")
    return items, modo


def calcular(db: Session, datos: CalculoRequest) -> dict:
    """Calcula la capacidad para un modelo o una placa. Recibe la peticion."""
    config = obtener_configuracion(db)

    if datos.placa:
        placa = datos.placa.strip().upper()
        vinculacion = capacidad_repository.obtener_vinculacion_por_placa(db, placa)
        if vinculacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La placa no tiene un modelo vinculado.",
            )
        modelo_id = vinculacion.modelo_id
        nombre_placa = placa
    else:
        modelo_id = datos.modelo_id
        nombre_placa = "CATALOGO"

    modelo = obtener_modelo(db, modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El modelo no existe en el catalogo.",
        )

    items, modo = _resolver_items(db, datos, tamanos_desde_config(config))
    factor = datos.factor_aprovechamiento or config.factor_aprovechamiento
    max_paradas = datos.max_paradas_por_viaje or config.max_paradas_por_viaje
    max_viajes = datos.max_viajes_por_dia or config.max_viajes_por_dia

    plan = calcular_plan(
        items,
        [vehiculo_desde_modelo(modelo, nombre_placa)],
        factor,
        max_paradas,
        max_viajes,
        config.max_paradas_por_jornada,
    )

    return {"modo": modo, "configuracion": configuracion_dict(config), **plan}


def planificacion(
    db: Session,
    filtros: FiltrosPedidos,
    demo_pedidos: Optional[int] = None,
    demo_vehiculos: Optional[int] = None,
    factor_aprovechamiento: Optional[float] = None,
    max_paradas_por_viaje: Optional[int] = None,
    max_viajes_por_dia: Optional[int] = None,
) -> dict:
    """Planifica el dia con la flota vinculada. Recibe filtros y ajustes."""
    config = obtener_configuracion(db)
    vehiculos, sin_modelo, no_disponibles = _flota_planificable(db)

    if demo_pedidos:
        items = items_demo(demo_pedidos, tamanos_desde_config(config))
        if demo_vehiculos:
            vehiculos = _vehiculos_demo(demo_vehiculos, vehiculos)
        modo = "demo"
    else:
        pedidos = capacidad_repository.listar_pedidos_planificables(
            db,
            estado=filtros.estado,
            distrito=filtros.distrito,
            fecha=filtros.fecha,
            limite=min(filtros.limite or MAX_PEDIDOS, MAX_PEDIDOS),
        )
        items = items_desde_pedidos(pedidos, tamanos_desde_config(config))
        modo = "pedidos"

    if len(items) > MAX_PEDIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La planificacion admite como maximo {MAX_PEDIDOS} pedidos.",
        )

    factor = factor_aprovechamiento or config.factor_aprovechamiento
    max_paradas = max_paradas_por_viaje or config.max_paradas_por_viaje
    max_viajes = max_viajes_por_dia or config.max_viajes_por_dia

    plan = calcular_plan(
        items,
        vehiculos,
        factor,
        max_paradas,
        max_viajes,
        config.max_paradas_por_jornada,
    )

    if not vehiculos:
        plan["alertas"].insert(
            0,
            {
                "nivel": "danger",
                "codigo": "flota_sin_vinculaciones",
                "mensaje": (
                    "Ningun vehiculo tiene modelo vinculado. Vincula placas en la "
                    "pestana Flota y vinculaciones."
                ),
            },
        )
    elif sin_modelo:
        plan["alertas"].append(
            {
                "nivel": "info",
                "codigo": "vehiculos_sin_modelo",
                "mensaje": (
                    f"{sin_modelo} vehiculos de la flota no tienen modelo vinculado "
                    "y quedaron fuera del plan."
                ),
            }
        )

    if no_disponibles and modo != "demo":
        plan["alertas"].append({
            "nivel": "warning", "codigo": "vehiculos_no_disponibles",
            "mensaje": f"{no_disponibles} vehiculos no pueden salir por estado, conductor o ruta activa.",
        })

    if modo == "demo":
        plan["alertas"].append(
            {
                "nivel": "info",
                "codigo": "escenario_demo",
                "mensaje": (
                    f"Escenario de demostracion con {len(items)} pedidos sinteticos "
                    "y capacidad tipica: no usa pedidos reales."
                ),
            }
        )

    return {"modo": modo, "configuracion": configuracion_dict(config), **plan}


def historial_auditoria(db: Session, limite: int = 100) -> List[dict]:
    """Devuelve los ultimos movimientos del modulo. Recibe la sesion y el limite."""
    return [
        {
            "id": fila.id,
            "accion": fila.accion,
            "entidad": fila.entidad,
            "entidad_id": fila.entidad_id,
            "detalle": fila.detalle,
            "usuario": fila.usuario,
            "creado_en": fila.creado_en,
        }
        for fila in capacidad_repository.listar_auditoria(db, limite)
    ]