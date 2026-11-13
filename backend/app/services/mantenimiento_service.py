# Logica del modulo de mantenimiento y documentos de la flota (Idea 4).
# No conoce HTTP: recibe datos, consulta el repositorio y devuelve diccionarios
# que el router convierte a los esquemas Pydantic. Solo LEE la tabla de vehiculos.
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.codigos import asignar_codigo
from app.models.mantenimiento import (
    ConfiguracionMantenimiento,
    DocumentoFlota,
    MantenimientoRegistro,
)
from app.repositories import mantenimiento_repository, vehiculo_repository
from app.schemas.mantenimiento import (
    CompletarMantenimientoRequest,
    ConfiguracionUpdateRequest,
    DocumentoCreateRequest,
    DocumentoUpdateRequest,
    EstadoDocumentoEnum,
    EstadoMantenimientoEnum,
    MantenimientoCreateRequest,
    MantenimientoUpdateRequest,
    TipoDocumentoEnum,
    TipoMantenimientoEnum,
)

PREFIJO_DOCUMENTO = "DC"
PREFIJO_MANTENIMIENTO = "MT"

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
    ultimo_kilometraje = max(kilometrajes) if kilometrajes else None

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

    return {
        "placa": vehiculo.placa,
        "marca": vehiculo.marca,
        "codigo": vehiculo.codigo,
        "estado_vehiculo": vehiculo.estado,
        "odometro_actual": ultimo_kilometraje,
        "documentos": [
            documento_dict(fila, hoy, config.dias_aviso_documento)
            for fila in documentos
        ],
        "mantenimientos": [
            mantenimiento_dict(fila, hoy) for fila in mantenimientos
        ],
        "costos": {
            "costo_total": round(costo_total, 2),
            "costo_mes": round(costo_mes, 2),
            "costo_por_kilometro": costo_por_kilometro,
            "moneda": config.moneda,
            "mantenimientos_completados": len(completados),
            "ultimo_kilometraje": ultimo_kilometraje,
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