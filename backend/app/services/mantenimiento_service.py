# Logica del modulo de mantenimiento y documentos de la flota (Idea 4).
# No conoce HTTP: recibe datos, consulta el repositorio y devuelve diccionarios
# que el router convierte a los esquemas Pydantic. Solo LEE la tabla de vehiculos.
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.codigos import asignar_codigo
from app.models.mantenimiento import (
    CargaCombustible,
    ConfiguracionMantenimiento,
    DocumentoFlota,
    MantenimientoRegistro,
    PlanPreventivo,
)
from app.repositories import mantenimiento_repository, vehiculo_repository
from app.schemas.mantenimiento import (
    CargaCombustibleCreateRequest,
    CargaCombustibleUpdateRequest,
    CompletarMantenimientoRequest,
    ConfiguracionUpdateRequest,
    DocumentoCreateRequest,
    DocumentoUpdateRequest,
    EstadoDocumentoEnum,
    EstadoMantenimientoEnum,
    EstadoPreventivoEnum,
    MantenimientoCreateRequest,
    MantenimientoUpdateRequest,
    PreventivoCreateRequest,
    PreventivoUpdateRequest,
    TipoCombustibleEnum,
    TipoDocumentoEnum,
    TipoMantenimientoEnum,
)

PREFIJO_DOCUMENTO = "DC"
PREFIJO_MANTENIMIENTO = "MT"
PREFIJO_PREVENTIVO = "PV"
PREFIJO_COMBUSTIBLE = "CB"

# Documentos minimos que debe tener todo vehiculo operativo.
DOCUMENTOS_OBLIGATORIOS = ("SOAT", "REVISION_TECNICA")

# Un mantenimiento sigue abierto mientras no se complete ni se cancele.
ESTADOS_ABIERTOS = ("PROGRAMADO", "EN_PROCESO")

# Umbrales de aviso de la consigna: 30, 15 y 7 dias antes del vencimiento.
UMBRALES_DOCUMENTO = (30, 15, 7)


# ---------------------------------------------------------------------------
# Reglas de estado (funciones puras, faciles de probar)
# ---------------------------------------------------------------------------


def calcular_estado_documento(
    fecha_vencimiento: date,
    hoy: Optional[date] = None,
    dias_aviso: int = 30,
) -> str:
    """Devuelve VENCIDO, POR_VENCER o VIGENTE. Recibe vencimiento, hoy y dias de aviso."""

    hoy = hoy or date.today()
    dias = (fecha_vencimiento - hoy).days
    if dias < 0:
        return EstadoDocumentoEnum.VENCIDO.value
    if dias <= dias_aviso:
        return EstadoDocumentoEnum.POR_VENCER.value
    return EstadoDocumentoEnum.VIGENTE.value


def dias_para_vencer(fecha_vencimiento: date, hoy: Optional[date] = None) -> int:
    """Devuelve los dias que faltan para el vencimiento (negativo si ya vencio)."""

    return (fecha_vencimiento - (hoy or date.today())).days


# Severidad de cada umbral de aviso: 30 dias avisa, 15 aprieta, 7 urge.
SEVERIDAD_POR_UMBRAL = {7: "ALTA", 15: "MEDIA", 30: "BAJA"}


def nivel_alerta_vencimiento(dias: int) -> tuple:
    """Devuelve (severidad, umbral) segun los dias que faltan. Recibe los dias.

    Regla de la consigna: avisos a 30, 15 y 7 dias. Un vencimiento ya pasado
    siempre es ALTA y no tiene umbral.
    """

    if dias < 0:
        return "ALTA", None
    for umbral in sorted(UMBRALES_DOCUMENTO):
        if dias <= umbral:
            return SEVERIDAD_POR_UMBRAL[umbral], umbral
    return "BAJA", max(UMBRALES_DOCUMENTO)


def _valor_enum(valor):
    """Convierte un Enum a su valor de texto; deja el resto igual. Recibe el valor."""

    return valor.value if hasattr(valor, "value") else valor


def _validar_no_nulos(cambios: dict, campos: tuple) -> None:
    """Rechaza un null explicito en campos obligatorios. Recibe los cambios."""

    for campo in campos:
        if campo in cambios and cambios[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El campo {campo} no puede ser nulo.",
            )


# ---------------------------------------------------------------------------
# Conversiones a respuesta
# ---------------------------------------------------------------------------


def documento_dict(
    fila: DocumentoFlota,
    hoy: Optional[date] = None,
    dias_aviso: int = 30,
) -> dict:
    """Arma el diccionario de respuesta de un documento. Recibe la fila y la config."""

    return {
        "id": fila.id,
        "codigo": fila.codigo,
        "placa": fila.placa,
        "tipo_documento": fila.tipo_documento,
        "numero": fila.numero,
        "entidad_emisora": fila.entidad_emisora,
        "fecha_emision": fila.fecha_emision,
        "fecha_vencimiento": fila.fecha_vencimiento,
        "archivo_url": fila.archivo_url,
        "observaciones": fila.observaciones,
        "estado": calcular_estado_documento(fila.fecha_vencimiento, hoy, dias_aviso),
        "dias_para_vencer": dias_para_vencer(fila.fecha_vencimiento, hoy),
        "creado_por": fila.creado_por,
        "creado_en": fila.creado_en,
        "actualizado_por": fila.actualizado_por,
        "actualizado_en": fila.actualizado_en,
    }


def mantenimiento_dict(
    fila: MantenimientoRegistro,
    hoy: Optional[date] = None,
) -> dict:
    """Arma el diccionario de respuesta de un mantenimiento. Recibe la fila."""

    hoy = hoy or date.today()
    dias = None
    if fila.fecha_programada is not None:
        dias = (fila.fecha_programada - hoy).days
    vencido = bool(
        fila.estado in ESTADOS_ABIERTOS
        and dias is not None
        and dias < 0
    )
    return {
        "id": fila.id,
        "codigo": fila.codigo,
        "placa": fila.placa,
        "tipo": fila.tipo,
        "categoria": fila.categoria,
        "descripcion": fila.descripcion,
        "prioridad": fila.prioridad,
        "estado": fila.estado,
        "fecha_programada": fila.fecha_programada,
        "fecha_ejecucion": fila.fecha_ejecucion,
        "kilometraje": fila.kilometraje,
        "costo": fila.costo,
        "moneda": fila.moneda,
        "taller": fila.taller,
        "observaciones": fila.observaciones,
        "vencido": vencido,
        "dias_para_programado": dias,
        "creado_por": fila.creado_por,
        "creado_en": fila.creado_en,
        "actualizado_por": fila.actualizado_por,
        "actualizado_en": fila.actualizado_en,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _vehiculo_por_placa(db: Session, placa: str):
    """Devuelve el vehiculo activo de esa placa o lanza 404. Recibe la sesion."""

    normalizada = (placa or "").strip().upper()
    vehiculo = vehiculo_repository.obtener_por_placa(db, normalizada)
    if vehiculo is None or vehiculo.eliminado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un vehículo activo con la placa {normalizada}.",
        )
    return vehiculo


def _validar_kilometraje(
    db: Session,
    placa: str,
    kilometraje: Optional[int],
    excluir_carga_id: Optional[int] = None,
    excluir_mantenimiento_id: Optional[int] = None,
) -> None:
    """Rechaza una lectura menor a la ultima registrada. Recibe la placa y el km.

    La regla de la consigna es que el kilometraje no puede retroceder. Se comparan
    las lecturas de mantenimiento y de combustible de la misma unidad.
    """

    if kilometraje is None:
        return
    lecturas = [
        fila.kilometraje
        for fila in mantenimiento_repository.listar_mantenimientos(db, placa=placa)
        if fila.kilometraje is not None
        and fila.id != excluir_mantenimiento_id
    ]
    lecturas.extend(
        fila.odometro
        for fila in mantenimiento_repository.listar_cargas(db, placa=placa)
        if fila.odometro is not None and fila.id != excluir_carga_id
    )
    if lecturas and kilometraje < max(lecturas):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"El kilometraje {kilometraje} es menor que la última lectura "
                f"registrada ({max(lecturas)}) para la placa {placa}."
            ),
        )


def _obtener_documento(db: Session, documento_id: int) -> DocumentoFlota:
    """Devuelve un documento activo o lanza 404. Recibe la sesion y el id."""

    fila = mantenimiento_repository.obtener_documento(db, documento_id)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El documento no existe o fue eliminado.",
        )
    return fila


def _obtener_mantenimiento(db: Session, mantenimiento_id: int) -> MantenimientoRegistro:
    """Devuelve un mantenimiento activo o lanza 404. Recibe la sesion y el id."""

    fila = mantenimiento_repository.obtener_mantenimiento(db, mantenimiento_id)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El mantenimiento no existe o fue eliminado.",
        )
    return fila


def _documentos_actuales(docs: List[DocumentoFlota]) -> List[DocumentoFlota]:
    """Devuelve el documento vigente por vehiculo y tipo. Recibe los documentos.

    Cada renovacion es una fila nueva. Manda la de vencimiento mas lejano; las
    anteriores quedan como historial y no definen estado ni generan alertas.
    """

    actuales: Dict[tuple, DocumentoFlota] = {}
    for fila in docs:
        clave = (fila.vehiculo_id, fila.tipo_documento)
        actual = actuales.get(clave)
        if actual is None or (fila.fecha_vencimiento, fila.id or 0) > (
            actual.fecha_vencimiento,
            actual.id or 0,
        ):
            actuales[clave] = fila
    return list(actuales.values())


def _estado_documental(
    docs_v: List[DocumentoFlota],
    config: ConfiguracionMantenimiento,
    hoy: date,
) -> dict:
    """Resume el estado documental de una unidad. Recibe sus documentos y la config.

    Calcula el estado general, los faltantes y la marca "no apto para salir".
    Solo cuenta la renovacion mas reciente de cada tipo. Nada de esto se guarda:
    se recalcula en cada consulta.
    """

    actuales = _documentos_actuales(docs_v)
    estados = [
        calcular_estado_documento(
            fila.fecha_vencimiento, hoy, config.dias_aviso_documento
        )
        for fila in actuales
    ]
    tipos = {fila.tipo_documento for fila in actuales}
    faltantes = [
        requerido
        for requerido in DOCUMENTOS_OBLIGATORIOS
        if requerido not in tipos
    ]

    if not actuales:
        estado_general = "SIN_DOCUMENTOS"
    elif EstadoDocumentoEnum.VENCIDO.value in estados:
        estado_general = "VENCIDO"
    elif faltantes:
        estado_general = "INCOMPLETO"
    elif EstadoDocumentoEnum.POR_VENCER.value in estados:
        estado_general = "POR_VENCER"
    else:
        estado_general = "AL_DIA"

    # "No apto para salir": algun documento actual vencido o falta un obligatorio.
    motivos = [
        f"{fila.tipo_documento} vencido"
        for fila, estado in zip(actuales, estados)
        if estado == EstadoDocumentoEnum.VENCIDO.value
    ]
    motivos.extend(f"Falta {requerido}" for requerido in faltantes)

    return {
        "documentos_total": len(actuales),
        "documentos_vencidos": estados.count(EstadoDocumentoEnum.VENCIDO.value),
        "documentos_por_vencer": estados.count(
            EstadoDocumentoEnum.POR_VENCER.value
        ),
        "documentos_faltantes": faltantes,
        "proximo_vencimiento": min(
            (fila.fecha_vencimiento for fila in actuales), default=None
        ),
        "estado_general": estado_general,
        "apto_para_salir": not motivos,
        "motivos_no_apto": motivos,
    }


# ---------------------------------------------------------------------------
# Documentos
# ---------------------------------------------------------------------------


def crear_documento(
    db: Session, datos: DocumentoCreateRequest, usuario: str
) -> dict:
    """Registra un documento de flota. Recibe datos y el correo del usuario."""

    vehiculo = _vehiculo_por_placa(db, datos.placa)
    duplicado = mantenimiento_repository.buscar_documento_duplicado(
        db, vehiculo.id, datos.tipo_documento.value, datos.numero
    )
    if duplicado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"La placa {vehiculo.placa} ya tiene un {datos.tipo_documento.value} "
                f"registrado con el número {datos.numero}."
            ),
        )

    campos = datos.model_dump(exclude={"placa"})
    campos["tipo_documento"] = datos.tipo_documento.value
    fila = DocumentoFlota(
        vehiculo_id=vehiculo.id,
        placa=vehiculo.placa,
        creado_por=usuario,
        **campos,
    )
    mantenimiento_repository.crear_documento(db, fila)
    asignar_codigo(db, fila, PREFIJO_DOCUMENTO)
    mantenimiento_repository.registrar_auditoria(
        db,
        "crear",
        "documento",
        fila.id,
        f"{fila.tipo_documento} {fila.numero} de {fila.placa}",
        usuario,
    )
    db.commit()
    db.refresh(fila)
    return documento_dict(fila)


def listar_documentos(
    db: Session,
    placa: Optional[str] = None,
    tipo: Optional[TipoDocumentoEnum] = None,
    estado: Optional[EstadoDocumentoEnum] = None,
    limite: int = 200,
    hoy: Optional[date] = None,
) -> List[dict]:
    """Lista documentos con su estado calculado. Recibe filtros opcionales."""

    config = obtener_configuracion(db)
    filas = mantenimiento_repository.listar_documentos(
        db,
        placa=(placa or "").strip().upper() or None,
        tipo_documento=tipo.value if tipo else None,
    )
    resultado = [
        documento_dict(fila, hoy, config.dias_aviso_documento) for fila in filas
    ]
    if estado is not None:
        # SIN_DOCUMENTO no es un estado de una fila: se calcula por vehiculo en /flota.
        resultado = [fila for fila in resultado if fila["estado"] == estado.value]
    return resultado[:limite]


def obtener_documento(
    db: Session, documento_id: int, hoy: Optional[date] = None
) -> dict:
    """Devuelve un documento con su estado calculado. Recibe la sesion y el id."""

    config = obtener_configuracion(db)
    return documento_dict(
        _obtener_documento(db, documento_id), hoy, config.dias_aviso_documento
    )


def actualizar_documento(
    db: Session,
    documento_id: int,
    datos: DocumentoUpdateRequest,
    usuario: str,
) -> dict:
    """Actualiza un documento y registra el cambio. Recibe datos y usuario."""

    fila = _obtener_documento(db, documento_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return documento_dict(fila, dias_aviso=obtener_configuracion(db).dias_aviso_documento)

    _validar_no_nulos(
        cambios,
        ("placa", "tipo_documento", "numero", "fecha_emision", "fecha_vencimiento"),
    )

    if "placa" in cambios:
        vehiculo = _vehiculo_por_placa(db, cambios.pop("placa"))
        fila.vehiculo_id = vehiculo.id
        fila.placa = vehiculo.placa

    for campo, valor in list(cambios.items()):
        cambios[campo] = _valor_enum(valor)

    tipo = cambios.get("tipo_documento", fila.tipo_documento)
    numero = cambios.get("numero", fila.numero)
    duplicado = mantenimiento_repository.buscar_documento_duplicado(
        db, fila.vehiculo_id, tipo, numero, excluir_id=fila.id
    )
    if duplicado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"La placa {fila.placa} ya tiene un {tipo} registrado "
                f"con el número {numero}."
            ),
        )

    emision = cambios.get("fecha_emision", fila.fecha_emision)
    vencimiento = cambios.get("fecha_vencimiento", fila.fecha_vencimiento)
    if emision is not None and vencimiento is not None and vencimiento <= emision:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha de vencimiento debe ser posterior a la fecha de emisión.",
        )

    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db,
        "editar",
        "documento",
        fila.id,
        ", ".join(cambios.keys()),
        usuario,
    )
    db.commit()
    db.refresh(fila)
    return documento_dict(
        fila, dias_aviso=obtener_configuracion(db).dias_aviso_documento
    )


def eliminar_documento(db: Session, documento_id: int, usuario: str) -> None:
    """Aplica baja logica a un documento y registra el cambio. Recibe el id."""

    fila = _obtener_documento(db, documento_id)
    fila.eliminado_en = datetime.utcnow()
    fila.actualizado_por = usuario
    fila.actualizado_en = fila.eliminado_en
    mantenimiento_repository.registrar_auditoria(
        db, "eliminar", "documento", fila.id, fila.numero, usuario
    )
    db.commit()


# ---------------------------------------------------------------------------
# Mantenimientos
# ---------------------------------------------------------------------------


def crear_mantenimiento(
    db: Session, datos: MantenimientoCreateRequest, usuario: str
) -> dict:
    """Programa o registra un mantenimiento. Recibe datos y el correo del usuario."""

    vehiculo = _vehiculo_por_placa(db, datos.placa)
    config = obtener_configuracion(db)

    campos = datos.model_dump(exclude={"placa"})
    _validar_kilometraje(db, vehiculo.placa, campos.get("kilometraje"))
    for campo in ("tipo", "categoria", "prioridad", "estado"):
        campos[campo] = _valor_enum(campos[campo])
    if campos["estado"] == EstadoMantenimientoEnum.COMPLETADO.value and campos.get(
        "fecha_ejecucion"
    ) is None:
        campos["fecha_ejecucion"] = date.today()

    fila = MantenimientoRegistro(
        vehiculo_id=vehiculo.id,
        placa=vehiculo.placa,
        moneda=config.moneda,
        creado_por=usuario,
        **campos,
    )
    mantenimiento_repository.crear_mantenimiento(db, fila)
    asignar_codigo(db, fila, PREFIJO_MANTENIMIENTO)
    mantenimiento_repository.registrar_auditoria(
        db,
        "crear",
        "mantenimiento",
        fila.id,
        f"{fila.tipo} {fila.categoria} de {fila.placa}",
        usuario,
    )
    db.commit()
    db.refresh(fila)
    return mantenimiento_dict(fila)


def listar_mantenimientos(
    db: Session,
    placa: Optional[str] = None,
    tipo: Optional[TipoMantenimientoEnum] = None,
    estado: Optional[EstadoMantenimientoEnum] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limite: int = 200,
    hoy: Optional[date] = None,
) -> List[dict]:
    """Lista mantenimientos con filtros opcionales. Recibe la sesion y los filtros."""

    filas = mantenimiento_repository.listar_mantenimientos(
        db,
        placa=(placa or "").strip().upper() or None,
        tipo=tipo.value if tipo else None,
        estado=estado.value if estado else None,
        desde=desde,
        hasta=hasta,
        limite=limite,
    )
    return [mantenimiento_dict(fila, hoy) for fila in filas]


def obtener_mantenimiento(
    db: Session, mantenimiento_id: int, hoy: Optional[date] = None
) -> dict:
    """Devuelve un mantenimiento por id. Recibe la sesion y el identificador."""

    return mantenimiento_dict(_obtener_mantenimiento(db, mantenimiento_id), hoy)


def actualizar_mantenimiento(
    db: Session,
    mantenimiento_id: int,
    datos: MantenimientoUpdateRequest,
    usuario: str,
) -> dict:
    """Actualiza un mantenimiento y registra el cambio. Recibe datos y usuario."""

    fila = _obtener_mantenimiento(db, mantenimiento_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return mantenimiento_dict(fila)

    _validar_no_nulos(
        cambios,
        (
            "placa",
            "tipo",
            "categoria",
            "descripcion",
            "prioridad",
            "estado",
            "fecha_programada",
        ),
    )

    if "placa" in cambios:
        vehiculo = _vehiculo_por_placa(db, cambios.pop("placa"))
        fila.vehiculo_id = vehiculo.id
        fila.placa = vehiculo.placa

    for campo, valor in list(cambios.items()):
        cambios[campo] = _valor_enum(valor)

    if "kilometraje" in cambios:
        _validar_kilometraje(
            db,
            fila.placa,
            cambios["kilometraje"],
            excluir_mantenimiento_id=fila.id,
        )

    nuevo_estado = cambios.get("estado", fila.estado)
    if nuevo_estado == EstadoMantenimientoEnum.COMPLETADO.value:
        fecha = cambios.get("fecha_ejecucion", fila.fecha_ejecucion)
        if fecha is None:
            cambios["fecha_ejecucion"] = date.today()

    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db,
        "editar",
        "mantenimiento",
        fila.id,
        ", ".join(cambios.keys()),
        usuario,
    )
    db.commit()
    db.refresh(fila)
    return mantenimiento_dict(fila)


def completar_mantenimiento(
    db: Session,
    mantenimiento_id: int,
    datos: CompletarMantenimientoRequest,
    usuario: str,
) -> dict:
    """Cierra un mantenimiento abierto con fecha, costo y kilometraje. Recibe el id."""

    fila = _obtener_mantenimiento(db, mantenimiento_id)
    if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El mantenimiento ya está completado.",
        )
    if fila.estado == EstadoMantenimientoEnum.CANCELADO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede completar un mantenimiento cancelado.",
        )

    cambios = datos.model_dump(exclude_unset=True)
    _validar_kilometraje(
        db,
        fila.placa,
        cambios.get("kilometraje"),
        excluir_mantenimiento_id=fila.id,
    )
    fila.estado = EstadoMantenimientoEnum.COMPLETADO.value
    fila.fecha_ejecucion = cambios.pop("fecha_ejecucion", None) or date.today()
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db, "completar", "mantenimiento", fila.id, fila.placa, usuario
    )
    db.commit()
    db.refresh(fila)
    return mantenimiento_dict(fila)


def eliminar_mantenimiento(
    db: Session, mantenimiento_id: int, usuario: str
) -> None:
    """Aplica baja logica a un mantenimiento y registra el cambio. Recibe el id."""

    fila = _obtener_mantenimiento(db, mantenimiento_id)
    fila.eliminado_en = datetime.utcnow()
    fila.actualizado_por = usuario
    fila.actualizado_en = fila.eliminado_en
    mantenimiento_repository.registrar_auditoria(
        db, "eliminar", "mantenimiento", fila.id, fila.codigo, usuario
    )
    db.commit()


# ---------------------------------------------------------------------------
# Semana 14: preventivos, averias, combustible y costos
# ---------------------------------------------------------------------------


def _obtener_preventivo(db: Session, preventivo_id: int) -> PlanPreventivo:
    """Devuelve un plan activo o lanza 404. Recibe la sesion y el id."""

    fila = mantenimiento_repository.obtener_preventivo(db, preventivo_id)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El plan preventivo no existe o fue eliminado.",
        )
    return fila


def _obtener_carga(db: Session, carga_id: int) -> CargaCombustible:
    """Devuelve una carga activa o lanza 404. Recibe la sesion y el id."""

    fila = mantenimiento_repository.obtener_carga(db, carga_id)
    if fila is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La carga de combustible no existe o fue eliminada.",
        )
    return fila


def kilometraje_actual(db: Session, placa: str) -> int:
    """Devuelve la lectura de km mas alta de una unidad. Recibe la sesion y placa.

    Toma las lecturas de mantenimiento, los odometros de combustible y los km de
    las rutas finalizadas. Ninguno de esos datos se modifica aqui.
    """

    lecturas = [
        fila.kilometraje
        for fila in mantenimiento_repository.listar_mantenimientos(db, placa=placa)
        if fila.kilometraje is not None
    ]
    lecturas.extend(
        fila.odometro
        for fila in mantenimiento_repository.listar_cargas(db, placa=placa)
        if fila.odometro is not None
    )
    lecturas.append(mantenimiento_repository.kilometraje_rutas(db, placa))
    return int(round(max(lecturas, default=0.0)))


def preventivo_dict(
    fila: PlanPreventivo,
    db: Session,
    hoy: Optional[date] = None,
    config: Optional[ConfiguracionMantenimiento] = None,
) -> dict:
    """Arma la respuesta de un plan con su estado calculado. Recibe la fila."""

    hoy = hoy or date.today()
    config = config or obtener_configuracion(db)
    km_base = fila.km_base or 0
    km_rutas = mantenimiento_repository.kilometraje_rutas(
        db, fila.placa, desde=fila.fecha_base
    )
    lecturas = [
        registro.kilometraje
        for registro in mantenimiento_repository.listar_mantenimientos(
            db, placa=fila.placa
        )
        if registro.kilometraje is not None
    ]
    lecturas.extend(
        carga.odometro
        for carga in mantenimiento_repository.listar_cargas(db, placa=fila.placa)
        if carga.odometro is not None
    )
    km_actual = int(round(max([km_base] + lecturas + [km_base + km_rutas])))
    km_restantes = max(0, km_base + fila.intervalo_km - km_actual)

    fecha_limite = None
    dias_restantes = None
    if fila.fecha_base is not None and fila.intervalo_dias is not None:
        fecha_limite = fila.fecha_base + timedelta(days=fila.intervalo_dias)
        dias_restantes = (fecha_limite - hoy).days

    if km_restantes == 0 or (dias_restantes is not None and dias_restantes < 0):
        estado = EstadoPreventivoEnum.VENCIDO.value
    elif not lecturas and km_rutas == 0 and fecha_limite is None:
        estado = EstadoPreventivoEnum.SIN_LECTURAS.value
    elif km_restantes <= round(fila.intervalo_km * 0.2) or (
        dias_restantes is not None
        and dias_restantes <= config.dias_aviso_mantenimiento
    ):
        estado = EstadoPreventivoEnum.PROXIMO.value
    else:
        estado = EstadoPreventivoEnum.AL_DIA.value

    return {
        "id": fila.id,
        "codigo": fila.codigo,
        "placa": fila.placa,
        "categoria": fila.categoria,
        "descripcion": fila.descripcion,
        "intervalo_km": fila.intervalo_km,
        "intervalo_dias": fila.intervalo_dias,
        "km_base": fila.km_base,
        "km_actual": km_actual,
        "km_restantes": km_restantes,
        "fecha_base": fila.fecha_base,
        "fecha_limite": fecha_limite,
        "dias_restantes": dias_restantes,
        "estado": estado,
        "activo": bool(fila.activo),
        "creado_por": fila.creado_por,
        "creado_en": fila.creado_en,
    }


def crear_preventivo(
    db: Session, datos: PreventivoCreateRequest, usuario: str
) -> dict:
    """Crea un plan preventivo. Recibe los datos y el correo del usuario."""

    vehiculo = _vehiculo_por_placa(db, datos.placa)
    campos = datos.model_dump(exclude={"placa"})
    campos["categoria"] = campos["categoria"].value
    if campos.get("km_base") is None:
        campos["km_base"] = kilometraje_actual(db, vehiculo.placa)
    if campos.get("fecha_base") is None:
        campos["fecha_base"] = date.today()

    fila = PlanPreventivo(
        vehiculo_id=vehiculo.id,
        placa=vehiculo.placa,
        creado_por=usuario,
        **campos,
    )
    mantenimiento_repository.crear_preventivo(db, fila)
    asignar_codigo(db, fila, PREFIJO_PREVENTIVO)
    mantenimiento_repository.registrar_auditoria(
        db,
        "crear",
        "preventivo",
        fila.id,
        f"{fila.categoria} de {fila.placa} cada {fila.intervalo_km} km",
        usuario,
    )
    db.commit()
    db.refresh(fila)
    return preventivo_dict(fila, db)


def listar_preventivos(
    db: Session,
    placa: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 200,
    hoy: Optional[date] = None,
) -> List[dict]:
    """Lista los planes con su estado calculado. Recibe filtros opcionales."""

    config = obtener_configuracion(db)
    filas = mantenimiento_repository.listar_preventivos(
        db,
        placa=(placa or "").strip().upper() or None,
        categoria=categoria,
        limite=limite,
    )
    return [preventivo_dict(fila, db, hoy, config) for fila in filas]


def obtener_preventivo(
    db: Session, preventivo_id: int, hoy: Optional[date] = None
) -> dict:
    """Devuelve un plan por id con su estado calculado. Recibe el identificador."""

    return preventivo_dict(_obtener_preventivo(db, preventivo_id), db, hoy)


def actualizar_preventivo(
    db: Session,
    preventivo_id: int,
    datos: PreventivoUpdateRequest,
    usuario: str,
) -> dict:
    """Edita un plan preventivo y registra el cambio. Recibe los datos."""

    fila = _obtener_preventivo(db, preventivo_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return preventivo_dict(fila, db)

    _validar_no_nulos(
        cambios, ("placa", "categoria", "descripcion", "intervalo_km")
    )
    if "placa" in cambios:
        vehiculo = _vehiculo_por_placa(db, cambios.pop("placa"))
        fila.vehiculo_id = vehiculo.id
        fila.placa = vehiculo.placa
    for campo, valor in list(cambios.items()):
        cambios[campo] = _valor_enum(valor)
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db, "editar", "preventivo", fila.id, ", ".join(cambios.keys()), usuario
    )
    db.commit()
    db.refresh(fila)
    return preventivo_dict(fila, db)


def eliminar_preventivo(db: Session, preventivo_id: int, usuario: str) -> None:
    """Aplica baja logica a un plan preventivo. Recibe el id."""

    fila = _obtener_preventivo(db, preventivo_id)
    fila.eliminado_en = datetime.utcnow()
    fila.activo = False
    fila.actualizado_por = usuario
    fila.actualizado_en = fila.eliminado_en
    mantenimiento_repository.registrar_auditoria(
        db, "eliminar", "preventivo", fila.id, fila.codigo, usuario
    )
    db.commit()


def ranking_averias(db: Session, limite: int = 20) -> List[dict]:
    """Ordena las unidades con mas incidencias de auxilio mecanico.

    Lee incidencias del nucleo en solo lectura y sugiere revision preventiva a
    las unidades con tres o mas averias, o dos o mas todavia abiertas.
    """

    agrupado: Dict[str, List] = {}
    for incidencia in mantenimiento_repository.listar_incidencias(db):
        placa = incidencia.vehiculo_placa
        if not placa:
            continue
        agrupado.setdefault(placa, []).append(incidencia)

    resultado = []
    for placa, filas in agrupado.items():
        abiertas = sum(1 for fila in filas if fila.estado == "ABIERTA")
        total = len(filas)
        sugerencia = (
            "Revisión preventiva sugerida"
            if total >= 3 or abiertas >= 2
            else "Seguimiento"
        )
        resultado.append(
            {
                "placa": placa,
                "total": total,
                "abiertas": abiertas,
                "resueltas": total - abiertas,
                "ultima_fecha": max(
                    (fila.creado_en.date() for fila in filas if fila.creado_en),
                    default=None,
                ),
                "sugerencia": sugerencia,
            }
        )
    resultado.sort(key=lambda fila: (-fila["total"], -fila["abiertas"], fila["placa"]))
    return resultado[:limite]


def _cargas_con_rendimiento(
    db: Session,
    filas: List[CargaCombustible],
    tolerancia: int = 20,
) -> List[dict]:
    """Calcula km recorridos, rendimiento y consumo anomalo de cada carga.

    El km entre cargas sale del odometro cuando hay lecturas; si no, de los km
    de las rutas finalizadas en ese periodo. El consumo se compara contra el
    promedio de la misma unidad.
    """

    ordenadas = sorted(filas, key=lambda fila: (fila.fecha, fila.id or 0))
    calculadas: List[dict] = []
    for indice, fila in enumerate(ordenadas):
        anterior = ordenadas[indice - 1] if indice else None
        if anterior is not None and fila.odometro and anterior.odometro:
            km = max(0, fila.odometro - anterior.odometro)
        elif anterior is not None:
            km = mantenimiento_repository.kilometraje_rutas(
                db, fila.placa, desde=anterior.fecha, hasta=fila.fecha
            )
        else:
            km = mantenimiento_repository.kilometraje_rutas(
                db,
                fila.placa,
                desde=fila.fecha - timedelta(days=30),
                hasta=fila.fecha,
            )
        rendimiento = round(km / fila.galones, 2) if km > 0 else None
        calculadas.append(
            {
                "id": fila.id,
                "codigo": fila.codigo,
                "placa": fila.placa,
                "fecha": fila.fecha,
                "tipo_combustible": fila.tipo_combustible,
                "galones": fila.galones,
                "monto": fila.monto,
                "odometro": fila.odometro,
                "proveedor": fila.proveedor,
                "observaciones": fila.observaciones,
                "km_recorridos": round(km, 2),
                "rendimiento_km_gal": rendimiento,
                "consumo_anomalo": False,
                "creado_por": fila.creado_por,
                "creado_en": fila.creado_en,
            }
        )

    por_placa: Dict[str, List[float]] = {}
    for fila in calculadas:
        if fila["rendimiento_km_gal"] is not None:
            por_placa.setdefault(fila["placa"], []).append(
                fila["rendimiento_km_gal"]
            )
    promedios = {
        placa: sum(valores) / len(valores)
        for placa, valores in por_placa.items()
        if valores
    }
    for fila in calculadas:
        rendimiento = fila["rendimiento_km_gal"]
        promedio = promedios.get(fila["placa"])
        if rendimiento is not None and promedio and promedio > 0:
            desvio = abs(rendimiento - promedio) / promedio * 100
            fila["consumo_anomalo"] = desvio > tolerancia
    return calculadas


def crear_carga(
    db: Session, datos: CargaCombustibleCreateRequest, usuario: str
) -> dict:
    """Registra una carga de combustible. Recibe los datos y el correo del usuario."""

    vehiculo = _vehiculo_por_placa(db, datos.placa)
    campos = datos.model_dump(exclude={"placa"})
    _validar_kilometraje(db, vehiculo.placa, campos.get("odometro"))
    campos["tipo_combustible"] = campos["tipo_combustible"].value

    fila = CargaCombustible(
        vehiculo_id=vehiculo.id,
        placa=vehiculo.placa,
        creado_por=usuario,
        **campos,
    )
    mantenimiento_repository.crear_carga(db, fila)
    asignar_codigo(db, fila, PREFIJO_COMBUSTIBLE)
    mantenimiento_repository.registrar_auditoria(
        db,
        "crear",
        "combustible",
        fila.id,
        f"{fila.galones} gal de {fila.placa} por S/ {fila.monto}",
        usuario,
    )
    db.commit()
    db.refresh(fila)
    # Se recalcula con el historial de la unidad para que el consumo anomalo
    # se compare contra el promedio real y no contra una sola carga.
    calculadas = listar_cargas(db, placa=fila.placa)
    return next(fila_cal for fila_cal in calculadas if fila_cal["id"] == fila.id)


def listar_cargas(
    db: Session,
    placa: Optional[str] = None,
    tipo: Optional[TipoCombustibleEnum] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    limite: int = 200,
) -> List[dict]:
    """Lista cargas con su rendimiento calculado. Recibe filtros opcionales."""

    filas = mantenimiento_repository.listar_cargas(
        db,
        placa=(placa or "").strip().upper() or None,
        tipo_combustible=tipo.value if tipo else None,
        desde=desde,
        hasta=hasta,
        limite=limite,
    )
    return _cargas_con_rendimiento(
        db, filas, obtener_configuracion(db).tolerancia_consumo
    )


def obtener_carga(db: Session, carga_id: int) -> dict:
    """Devuelve una carga por id con su rendimiento. Recibe el identificador."""

    fila = _obtener_carga(db, carga_id)
    return _cargas_con_rendimiento(
        db, [fila], obtener_configuracion(db).tolerancia_consumo
    )[0]


def actualizar_carga(
    db: Session,
    carga_id: int,
    datos: CargaCombustibleUpdateRequest,
    usuario: str,
) -> dict:
    """Edita una carga y registra el cambio. Recibe los datos."""

    fila = _obtener_carga(db, carga_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return obtener_carga(db, carga_id)

    _validar_no_nulos(cambios, ("placa", "fecha", "galones", "monto"))
    if "placa" in cambios:
        vehiculo = _vehiculo_por_placa(db, cambios.pop("placa"))
        fila.vehiculo_id = vehiculo.id
        fila.placa = vehiculo.placa
    for campo, valor in list(cambios.items()):
        cambios[campo] = _valor_enum(valor)
    if "odometro" in cambios:
        _validar_kilometraje(
            db, fila.placa, cambios["odometro"], excluir_carga_id=fila.id
        )
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.actualizado_por = usuario
    fila.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db, "editar", "combustible", fila.id, ", ".join(cambios.keys()), usuario
    )
    db.commit()
    db.refresh(fila)
    return obtener_carga(db, carga_id)


def eliminar_carga(db: Session, carga_id: int, usuario: str) -> None:
    """Aplica baja logica a una carga y registra el cambio. Recibe el id."""

    fila = _obtener_carga(db, carga_id)
    fila.eliminado_en = datetime.utcnow()
    fila.actualizado_por = usuario
    fila.actualizado_en = fila.eliminado_en
    mantenimiento_repository.registrar_auditoria(
        db, "eliminar", "combustible", fila.id, fila.codigo, usuario
    )
    db.commit()


def costos_flota(db: Session, hoy: Optional[date] = None) -> dict:
    """Devuelve costos y rendimiento global de mantenimiento y combustible."""

    hoy = hoy or date.today()
    config = obtener_configuracion(db)
    mantenimientos = mantenimiento_repository.listar_mantenimientos(db)
    completados = [
        fila
        for fila in mantenimientos
        if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value
    ]
    cargas = listar_cargas(db, limite=5000)
    preventivos = listar_preventivos(db, hoy=hoy, limite=5000)

    costo_mantenimiento = sum((fila.costo or 0.0) for fila in completados)
    costo_combustible = sum((fila["monto"] or 0.0) for fila in cargas)
    km_totales = sum((fila["km_recorridos"] or 0.0) for fila in cargas)
    galones_totales = sum((fila["galones"] or 0.0) for fila in cargas)
    costo_total = costo_mantenimiento + costo_combustible

    return {
        "costo_mantenimiento": round(costo_mantenimiento, 2),
        "costo_combustible": round(costo_combustible, 2),
        "costo_total": round(costo_total, 2),
        "km_totales": round(km_totales, 2),
        "costo_por_kilometro": (
            round(costo_total / km_totales, 4) if km_totales > 0 else None
        ),
        "galones_totales": round(galones_totales, 2),
        "rendimiento_km_gal": (
            round(km_totales / galones_totales, 2) if galones_totales > 0 else None
        ),
        "cargas_totales": len(cargas),
        "mantenimientos_completados": len(completados),
        "preventivos_vencidos": sum(
            1 for fila in preventivos if fila["estado"] == EstadoPreventivoEnum.VENCIDO.value
        ),
        "moneda": config.moneda,
    }


# ---------------------------------------------------------------------------
# Configuracion y auditoria
# ---------------------------------------------------------------------------


def obtener_configuracion(db: Session) -> ConfiguracionMantenimiento:
    """Devuelve la configuracion y crea la fila por defecto si falta. Recibe la sesion."""

    config = mantenimiento_repository.obtener_configuracion(db)
    if config is not None:
        return config

    config = ConfiguracionMantenimiento(
        id=1,
        dias_aviso_documento=30,
        dias_aviso_mantenimiento=7,
        moneda="PEN",
        alertas_documentos=True,
        alertas_mantenimientos=True,
        tolerancia_consumo=20,
    )
    mantenimiento_repository.guardar_configuracion(db, config)
    try:
        db.commit()
    except Exception:
        # Otro proceso pudo crearla al mismo tiempo: se relee.
        db.rollback()
        config = mantenimiento_repository.obtener_configuracion(db)
        if config is None:
            raise
        return config
    db.refresh(config)
    return config


def configuracion_dict(config: ConfiguracionMantenimiento) -> dict:
    """Arma la respuesta de configuracion. Recibe la fila."""

    return {
        "dias_aviso_documento": config.dias_aviso_documento,
        "dias_aviso_mantenimiento": config.dias_aviso_mantenimiento,
        "moneda": config.moneda,
        "alertas_documentos": config.alertas_documentos,
        "alertas_mantenimientos": config.alertas_mantenimientos,
        "tolerancia_consumo": config.tolerancia_consumo or 20,
        "actualizado_por": config.actualizado_por,
        "actualizado_en": config.actualizado_en,
    }


def actualizar_configuracion(
    db: Session, datos: ConfiguracionUpdateRequest, usuario: str
) -> dict:
    """Cambia los parametros del modulo y registra el cambio. Recibe los datos."""

    config = obtener_configuracion(db)
    cambios = datos.model_dump(exclude_unset=True)
    _validar_no_nulos(cambios, tuple(cambios.keys()))
    for campo, valor in cambios.items():
        setattr(config, campo, valor)
    config.actualizado_por = usuario
    config.actualizado_en = datetime.utcnow()
    mantenimiento_repository.registrar_auditoria(
        db,
        "editar",
        "configuracion",
        str(config.id),
        ", ".join(cambios.keys()),
        usuario,
    )
    db.commit()
    db.refresh(config)
    return configuracion_dict(config)


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
        for fila in mantenimiento_repository.listar_auditoria(db, limite)
    ]


# ---------------------------------------------------------------------------
# Licencias de conductores (solo lectura del nucleo)
# ---------------------------------------------------------------------------


def licencia_dict(
    perfil,
    usuario,
    hoy: Optional[date] = None,
    dias_aviso: int = 30,
) -> dict:
    """Arma la respuesta de una licencia. Recibe el perfil y su usuario.

    El modulo NO edita la licencia: solo lee conductor_perfiles y calcula su
    estado y nivel de alerta.
    """

    hoy = hoy or date.today()
    vencimiento = perfil.licencia_vencimiento

    if vencimiento is None:
        estado = EstadoDocumentoEnum.SIN_DOCUMENTO.value
        dias = None
        nivel = None
        umbral = None
    else:
        estado = calcular_estado_documento(vencimiento, hoy, dias_aviso)
        dias = dias_para_vencer(vencimiento, hoy)
        if estado == EstadoDocumentoEnum.VIGENTE.value:
            nivel, umbral = None, None
        else:
            nivel, umbral = nivel_alerta_vencimiento(dias)

    return {
        "conductor_id": perfil.id,
        "usuario_id": perfil.usuario_id,
        "nombre": perfil.nombre,
        "correo": usuario.correo,
        "dni": perfil.dni,
        "licencia_numero": perfil.licencia_numero,
        "licencia_vencimiento": vencimiento,
        "estado": estado,
        "dias_para_vencer": dias,
        "nivel_alerta": nivel,
        "umbral": umbral,
    }


def listar_licencias(db: Session, hoy: Optional[date] = None) -> List[dict]:
    """Lista las licencias de los conductores con su estado calculado.

    Solo debe exponerse al administrador: son datos personales.
    """

    dias_aviso = obtener_configuracion(db).dias_aviso_documento
    return [
        licencia_dict(perfil, usuario, hoy, dias_aviso)
        for perfil, usuario in mantenimiento_repository.listar_licencias(db)
    ]


# ---------------------------------------------------------------------------
# Alertas, resumen y estado de la flota
# ---------------------------------------------------------------------------


def alertas(
    db: Session,
    hoy: Optional[date] = None,
    incluir_licencias: bool = False,
) -> List[dict]:
    """Calcula los avisos del dia: documentos, licencias y mantenimientos.

    Recibe la sesion. Las licencias solo se incluyen si incluir_licencias=True,
    que el router activa unicamente para administradores.
    """

    config = obtener_configuracion(db)
    hoy = hoy or date.today()
    resultado: List[dict] = []
    documentos = mantenimiento_repository.listar_documentos(db)
    actuales = _documentos_actuales(documentos)
    vehiculos = vehiculo_repository.listar(db)

    if config.alertas_documentos:
        for fila in actuales:
            estado = calcular_estado_documento(
                fila.fecha_vencimiento, hoy, config.dias_aviso_documento
            )
            dias = dias_para_vencer(fila.fecha_vencimiento, hoy)
            if estado == EstadoDocumentoEnum.VENCIDO.value:
                resultado.append(
                    {
                        "id": f"doc-{fila.id}-vencido",
                        "tipo": "DOCUMENTO",
                        "severidad": "ALTA",
                        "placa": fila.placa,
                        "conductor": None,
                        "titulo": f"{fila.tipo_documento} vencido",
                        "mensaje": (
                            f"La placa {fila.placa} tiene el {fila.tipo_documento} "
                            f"vencido desde el {fila.fecha_vencimiento}."
                        ),
                        "fecha_referencia": fila.fecha_vencimiento,
                        "dias": dias,
                        "umbral": None,
                        "entidad_id": fila.id,
                    }
                )
            elif estado == EstadoDocumentoEnum.POR_VENCER.value:
                severidad, umbral = nivel_alerta_vencimiento(dias)
                resultado.append(
                    {
                        "id": f"doc-{fila.id}-por-vencer",
                        "tipo": "DOCUMENTO",
                        "severidad": severidad,
                        "placa": fila.placa,
                        "conductor": None,
                        "titulo": f"{fila.tipo_documento} por vencer",
                        "mensaje": (
                            f"El {fila.tipo_documento} de la placa {fila.placa} "
                            f"vence en {dias} día(s), el {fila.fecha_vencimiento}."
                        ),
                        "fecha_referencia": fila.fecha_vencimiento,
                        "dias": dias,
                        "umbral": umbral,
                        "entidad_id": fila.id,
                    }
                )

        for vehiculo in vehiculos:
            tipos = {
                fila.tipo_documento
                for fila in actuales
                if fila.vehiculo_id == vehiculo.id
            }
            for requerido in DOCUMENTOS_OBLIGATORIOS:
                if requerido not in tipos:
                    resultado.append(
                        {
                            "id": f"veh-{vehiculo.id}-falta-{requerido}",
                            "tipo": "SIN_DOCUMENTO",
                            "severidad": "MEDIA",
                            "placa": vehiculo.placa,
                            "conductor": None,
                            "titulo": f"Falta {requerido}",
                            "mensaje": (
                                f"La placa {vehiculo.placa} no tiene registrado "
                                f"el documento {requerido}."
                            ),
                            "fecha_referencia": None,
                            "dias": None,
                            "umbral": None,
                            "entidad_id": vehiculo.id,
                        }
                    )

        if incluir_licencias:
            for perfil, _usuario in mantenimiento_repository.listar_licencias(db):
                if perfil.licencia_vencimiento is None:
                    continue
                estado = calcular_estado_documento(
                    perfil.licencia_vencimiento, hoy, config.dias_aviso_documento
                )
                if estado == EstadoDocumentoEnum.VIGENTE.value:
                    continue
                dias = dias_para_vencer(perfil.licencia_vencimiento, hoy)
                severidad, umbral = nivel_alerta_vencimiento(dias)
                if estado == EstadoDocumentoEnum.VENCIDO.value:
                    titulo = "Licencia de conducir vencida"
                    mensaje = (
                        f"La licencia de {perfil.nombre} venció el "
                        f"{perfil.licencia_vencimiento}."
                    )
                else:
                    titulo = "Licencia de conducir por vencer"
                    mensaje = (
                        f"La licencia de {perfil.nombre} vence en {dias} día(s), "
                        f"el {perfil.licencia_vencimiento}."
                    )
                resultado.append(
                    {
                        "id": f"lic-{perfil.id}",
                        "tipo": "LICENCIA",
                        "severidad": severidad,
                        "placa": None,
                        "conductor": perfil.nombre,
                        "titulo": titulo,
                        "mensaje": mensaje,
                        "fecha_referencia": perfil.licencia_vencimiento,
                        "dias": dias,
                        "umbral": umbral,
                        "entidad_id": perfil.id,
                    }
                )

    if config.alertas_mantenimientos:
        for fila in mantenimiento_repository.listar_mantenimientos(db):
            if fila.estado not in ESTADOS_ABIERTOS or fila.fecha_programada is None:
                continue
            dias = (fila.fecha_programada - hoy).days
            if dias < 0:
                severidad = "ALTA"
                titulo = "Mantenimiento vencido"
                mensaje = (
                    f"El mantenimiento {fila.codigo} de la placa {fila.placa} "
                    f"estaba programado para el {fila.fecha_programada}."
                )
            elif dias == 0:
                severidad = "ALTA"
                titulo = "Mantenimiento para hoy"
                mensaje = (
                    f"El mantenimiento {fila.codigo} de la placa {fila.placa} "
                    f"está programado para hoy."
                )
            elif dias <= config.dias_aviso_mantenimiento:
                severidad = "MEDIA"
                titulo = "Mantenimiento próximo"
                mensaje = (
                    f"El mantenimiento {fila.codigo} de la placa {fila.placa} "
                    f"vence en {dias} día(s)."
                )
            else:
                continue
            resultado.append(
                {
                    "id": f"mant-{fila.id}",
                    "tipo": "MANTENIMIENTO",
                    "severidad": severidad,
                    "placa": fila.placa,
                    "conductor": None,
                    "titulo": titulo,
                    "mensaje": mensaje,
                    "fecha_referencia": fila.fecha_programada,
                    "dias": dias,
                    "umbral": None,
                    "entidad_id": fila.id,
                }
            )

    if config.alertas_mantenimientos:
        for plan in listar_preventivos(db, hoy=hoy, limite=500):
            if plan["estado"] not in (
                EstadoPreventivoEnum.VENCIDO.value,
                EstadoPreventivoEnum.PROXIMO.value,
            ):
                continue
            vencido = plan["estado"] == EstadoPreventivoEnum.VENCIDO.value
            resultado.append(
                {
                    "id": f"prev-{plan['id']}",
                    "tipo": "PREVENTIVO",
                    "severidad": "ALTA" if vencido else "MEDIA",
                    "placa": plan["placa"],
                    "conductor": None,
                    "titulo": (
                        "Preventivo vencido" if vencido else "Preventivo próximo"
                    ),
                    "mensaje": (
                        f"El plan {plan['codigo']} ({plan['categoria']}) de la placa "
                        f"{plan['placa']} tiene {plan['km_restantes']} km restantes."
                    ),
                    "fecha_referencia": plan["fecha_limite"],
                    "dias": plan["dias_restantes"],
                    "umbral": config.dias_aviso_mantenimiento,
                    "entidad_id": plan["id"],
                }
            )
        for carga in listar_cargas(db, limite=500):
            if not carga["consumo_anomalo"]:
                continue
            resultado.append(
                {
                    "id": f"comb-{carga['id']}",
                    "tipo": "COMBUSTIBLE",
                    "severidad": "MEDIA",
                    "placa": carga["placa"],
                    "conductor": None,
                    "titulo": "Consumo anómalo",
                    "mensaje": (
                        f"La carga {carga['codigo']} de la placa {carga['placa']} "
                        f"rindió {carga['rendimiento_km_gal']} km/gal, fuera del "
                        f"promedio de la unidad."
                    ),
                    "fecha_referencia": carga["fecha"],
                    "dias": None,
                    "umbral": config.tolerancia_consumo,
                    "entidad_id": carga["id"],
                }
            )

    resultado.sort(
        key=lambda aviso: (
            0 if aviso["severidad"] == "ALTA" else 1,
            aviso["dias"] if aviso["dias"] is not None else 9999,
            aviso.get("placa") or aviso.get("conductor") or "",
        )
    )
    return resultado


def resumen(
    db: Session,
    hoy: Optional[date] = None,
    incluir_licencias: bool = False,
) -> dict:
    """Calcula los indicadores del modulo. Recibe la sesion y la fecha de corte.

    Las alertas de licencias solo se cuentan si incluir_licencias=True, que el
    router activa unicamente para administradores.
    """

    config = obtener_configuracion(db)
    hoy = hoy or date.today()
    documentos = mantenimiento_repository.listar_documentos(db)
    actuales = _documentos_actuales(documentos)
    mantenimientos = mantenimiento_repository.listar_mantenimientos(db)
    vehiculos = vehiculo_repository.listar(db)

    estados = [
        calcular_estado_documento(
            fila.fecha_vencimiento, hoy, config.dias_aviso_documento
        )
        for fila in actuales
    ]
    por_tipo: Dict[str, int] = {}
    for fila in actuales:
        por_tipo[fila.tipo_documento] = por_tipo.get(fila.tipo_documento, 0) + 1

    costo_mes = sum(
        (fila.costo or 0.0)
        for fila in mantenimientos
        if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value
        and fila.fecha_ejecucion is not None
        and fila.fecha_ejecucion.year == hoy.year
        and fila.fecha_ejecucion.month == hoy.month
    )
    costo_total = sum(
        (fila.costo or 0.0)
        for fila in mantenimientos
        if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value
    )
    avisos = alertas(db, hoy, incluir_licencias=incluir_licencias)
    sin_documentos = sum(
        1
        for vehiculo in vehiculos
        if not any(fila.vehiculo_id == vehiculo.id for fila in actuales)
    )
    # La semana 14 suma indicadores de preventivos, combustible y costos. El
    # costo_total historico se mantiene como gasto de mantenimiento solamente.
    cargas = listar_cargas(db, limite=5000)
    preventivos = listar_preventivos(db, hoy=hoy, limite=5000)
    costo_combustible = sum((fila["monto"] or 0.0) for fila in cargas)
    km_cargas = sum((fila["km_recorridos"] or 0.0) for fila in cargas)
    galones = sum((fila["galones"] or 0.0) for fila in cargas)

    return {
        "total_vehiculos": len(vehiculos),
        "documentos_total": len(actuales),
        "documentos_vigentes": estados.count(EstadoDocumentoEnum.VIGENTE.value),
        "documentos_por_vencer": estados.count(EstadoDocumentoEnum.POR_VENCER.value),
        "documentos_vencidos": estados.count(EstadoDocumentoEnum.VENCIDO.value),
        "documentos_por_tipo": por_tipo,
        "mantenimientos_total": len(mantenimientos),
        "mantenimientos_programados": sum(
            1
            for fila in mantenimientos
            if fila.estado == EstadoMantenimientoEnum.PROGRAMADO.value
        ),
        "mantenimientos_en_proceso": sum(
            1
            for fila in mantenimientos
            if fila.estado == EstadoMantenimientoEnum.EN_PROCESO.value
        ),
        "mantenimientos_completados": sum(
            1
            for fila in mantenimientos
            if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value
        ),
        "mantenimientos_vencidos": sum(
            1
            for fila in mantenimientos
            if fila.estado in ESTADOS_ABIERTOS
            and fila.fecha_programada is not None
            and fila.fecha_programada < hoy
        ),
        "costo_mes": round(costo_mes, 2),
        "costo_total": round(costo_total, 2),
        "costo_combustible": round(costo_combustible, 2),
        "costo_por_kilometro": (
            round((costo_total + costo_combustible) / km_cargas, 4)
            if km_cargas > 0
            else None
        ),
        "rendimiento_km_gal": round(km_cargas / galones, 2) if galones > 0 else None,
        "preventivos_vencidos": sum(
            1
            for fila in preventivos
            if fila["estado"] == EstadoPreventivoEnum.VENCIDO.value
        ),
        "consumos_anomalos": sum(1 for fila in cargas if fila["consumo_anomalo"]),
        "moneda": config.moneda,
        "alertas_total": len(avisos),
        "alertas_alta": sum(1 for aviso in avisos if aviso["severidad"] == "ALTA"),
        "vehiculos_sin_documentos": sin_documentos,
    }


def estado_flota(db: Session, hoy: Optional[date] = None) -> List[dict]:
    """Devuelve el estado documental y de mantenimiento de cada vehiculo."""

    config = obtener_configuracion(db)
    hoy = hoy or date.today()
    documentos = mantenimiento_repository.listar_documentos(db)
    mantenimientos = mantenimiento_repository.listar_mantenimientos(db)
    vehiculos = vehiculo_repository.listar(db)
    resultado: List[dict] = []

    for vehiculo in vehiculos:
        docs_v = [fila for fila in documentos if fila.vehiculo_id == vehiculo.id]
        mant_v = [fila for fila in mantenimientos if fila.vehiculo_id == vehiculo.id]
        abiertos = [
            fila for fila in mant_v if fila.estado in ESTADOS_ABIERTOS
        ]

        resultado.append(
            {
                "placa": vehiculo.placa,
                "marca": vehiculo.marca,
                "estado_vehiculo": vehiculo.estado,
                **_estado_documental(docs_v, config, hoy),
                "mantenimientos_abiertos": len(abiertos),
                "proximo_mantenimiento": min(
                    (
                        fila.fecha_programada
                        for fila in abiertos
                        if fila.fecha_programada is not None
                    ),
                    default=None,
                ),
            }
        )

    return resultado


def ficha_vehiculo(
    db: Session, placa: str, hoy: Optional[date] = None
) -> dict:
    """Devuelve la ficha completa de una unidad. Recibe la sesion y la placa.

    Junta en una sola vista los datos del vehiculo (solo lectura del nucleo),
    sus documentos, sus mantenimientos y sus costos.
    """

    config = obtener_configuracion(db)
    hoy = hoy or date.today()
    vehiculo = _vehiculo_por_placa(db, placa)
    documentos = mantenimiento_repository.listar_documentos(
        db, placa=vehiculo.placa
    )
    mantenimientos = mantenimiento_repository.listar_mantenimientos(
        db, placa=vehiculo.placa
    )
    abiertos = [
        fila for fila in mantenimientos if fila.estado in ESTADOS_ABIERTOS
    ]
    completados = [
        fila
        for fila in mantenimientos
        if fila.estado == EstadoMantenimientoEnum.COMPLETADO.value
    ]

    costo_total = sum((fila.costo or 0.0) for fila in completados)
    costo_mes = sum(
        (fila.costo or 0.0)
        for fila in completados
        if fila.fecha_ejecucion is not None
        and fila.fecha_ejecucion.year == hoy.year
        and fila.fecha_ejecucion.month == hoy.month
    )
    kilometrajes = [
        fila.kilometraje
        for fila in mantenimientos
        if fila.kilometraje is not None
    ]
    cargas = listar_cargas(db, placa=vehiculo.placa)
    kilometrajes.extend(
        fila["odometro"] for fila in cargas if fila["odometro"] is not None
    )
    km_rutas = mantenimiento_repository.kilometraje_rutas(db, vehiculo.placa)
    ultimo_kilometraje = max(kilometrajes + [km_rutas]) if kilometrajes or km_rutas else None

    completados_con_km = [
        fila for fila in completados if fila.kilometraje is not None
    ]
    kms = [fila.kilometraje for fila in completados_con_km]
    rango_km = (max(kms) - min(kms)) if len(kms) >= 2 else 0
    costo_por_kilometro = (
        round(
            sum((fila.costo or 0.0) for fila in completados_con_km) / rango_km,
            4,
        )
        if rango_km > 0
        else None
    )
    costo_combustible = sum((fila["monto"] or 0.0) for fila in cargas)
    galones = sum((fila["galones"] or 0.0) for fila in cargas)
    km_cargas = sum((fila["km_recorridos"] or 0.0) for fila in cargas)
    rendimiento = round(km_cargas / galones, 2) if galones > 0 else None
    preventivos = listar_preventivos(db, placa=vehiculo.placa, hoy=hoy)
    averias = [
        fila for fila in ranking_averias(db) if fila["placa"] == vehiculo.placa
    ]

    return {
        "placa": vehiculo.placa,
        "marca": vehiculo.marca,
        "codigo": vehiculo.codigo,
        "estado_vehiculo": vehiculo.estado,
        "odometro_actual": (
            int(round(ultimo_kilometraje)) if ultimo_kilometraje is not None else None
        ),
        "documentos": [
            documento_dict(fila, hoy, config.dias_aviso_documento)
            for fila in documentos
        ],
        "mantenimientos": [
            mantenimiento_dict(fila, hoy) for fila in mantenimientos
        ],
        "preventivos": preventivos,
        "cargas": cargas,
        "averias": averias,
        "costos": {
            "costo_total": round(costo_total + costo_combustible, 2),
            "costo_mes": round(costo_mes, 2),
            "costo_mantenimiento": round(costo_total, 2),
            "costo_combustible": round(costo_combustible, 2),
            "costo_por_kilometro": costo_por_kilometro,
            "rendimiento_km_gal": rendimiento,
            "moneda": config.moneda,
            "mantenimientos_completados": len(completados),
            "cargas_totales": len(cargas),
            "ultimo_kilometraje": (
                int(round(ultimo_kilometraje)) if ultimo_kilometraje is not None else None
            ),
        },
        **_estado_documental(documentos, config, hoy),
        "mantenimientos_abiertos": len(abiertos),
        "proximo_mantenimiento": min(
            (
                fila.fecha_programada
                for fila in abiertos
                if fila.fecha_programada is not None
            ),
            default=None,
        ),
    }