import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.repositories import verificacion_repository as repo

LIMITE_INTENTOS = 3
BLOQUEO_DNI_SEG = 30       # primer bloqueo tras 3 intentos fallidos de DNI (persona)
BLOQUEO_OTP_SEG = 45       # primer bloqueo tras 3 intentos fallidos de OTP (empresa)

# Bloqueo progresivo (C42-01): cada bloqueo seguido dura mas. El DNI son solo 4 digitos,
# asi que un bloqueo fijo de 30 s permitiria probar las 10 000 combinaciones en un dia.
ESCALONES_BLOQUEO_SEG = (120, 600, 1800, 3600)
OLVIDO_BLOQUEOS = timedelta(hours=24)   # tras un dia sin bloqueos se vuelve al primero


def segundos_de_bloqueo(base_seg: int, nivel: int) -> int:
    """Duracion del bloqueo segun cuantos bloqueos seguidos hubo. Recibe el bloqueo base y el nivel (0 = primero)."""
    if nivel <= 0:
        return base_seg
    return ESCALONES_BLOQUEO_SEG[min(nivel - 1, len(ESCALONES_BLOQUEO_SEG) - 1)]


def _nivel_actual(reg) -> int:
    """Nivel de bloqueo vigente del reto; se reinicia si el ultimo bloqueo fue hace mas de un dia. Recibe el reto."""
    if not reg or not reg.bloqueos:
        return 0
    if reg.bloqueado_hasta and datetime.utcnow() - reg.bloqueado_hasta > OLVIDO_BLOQUEOS:
        return 0
    return reg.bloqueos


def gen_otp() -> str:
    """Genera un OTP de 6 digitos criptograficamente aleatorio. Sin input."""
    return f"{secrets.randbelow(900000) + 100000}"


def evaluar_intento(intentos_previos: int, exito: bool, limite: int, bloqueo_seg: int) -> dict:
    """Politica pura de intentos. Recibe intentos previos, si acerto, el limite y los seg de bloqueo.
    Devuelve {ok} en exito, o {bloquear, intentos_restantes, bloqueo_seg} en fallo."""
    if exito:
        return {"ok": True}
    intentos = intentos_previos + 1
    if intentos >= limite:
        return {"ok": False, "bloquear": True, "intentos_restantes": 0, "bloqueo_seg": bloqueo_seg}
    return {"ok": False, "bloquear": False, "intentos_restantes": limite - intentos, "bloqueo_seg": bloqueo_seg}


def _exigir_no_bloqueado(reg):
    """Lanza 429 si el reto esta bloqueado ahora mismo. Recibe el registro (o None)."""
    if reg and reg.bloqueado_hasta and reg.bloqueado_hasta > datetime.utcnow():
        seg = int((reg.bloqueado_hasta - datetime.utcnow()).total_seconds()) + 1
        raise HTTPException(status_code=429, detail={"bloqueadoSegundos": seg})


def _aplicar_fallo(db, reg, tipo, referencia, bloqueo_seg):
    """Suma un intento y bloquea si toca (cada bloqueo seguido mas largo); lanza 401/429. Recibe reto, tipo, referencia y bloqueo base."""
    previos = reg.intentos if reg else 0
    r = evaluar_intento(previos, exito=False, limite=LIMITE_INTENTOS, bloqueo_seg=bloqueo_seg)
    if r["bloquear"]:
        nivel = _nivel_actual(reg)
        seg = segundos_de_bloqueo(bloqueo_seg, nivel)
        repo.upsert(db, tipo, referencia, intentos=0, bloqueos=nivel + 1,
                    bloqueado_hasta=datetime.utcnow() + timedelta(seconds=seg))
        repo.guardar(db)
        raise HTTPException(status_code=429, detail={"bloqueadoSegundos": seg})
    repo.upsert(db, tipo, referencia, intentos=previos + 1)
    repo.guardar(db)
    raise HTTPException(status_code=401, detail={"intentosRestantes": r["intentos_restantes"]})


def verificar_dni(db: Session, codigo: str, dni_ingresado: str | None, dni_real: str | None) -> None:
    """Valida los ultimos 4 del DNI contra el pedido. Recibe codigo, dni ingresado y dni real (o None).
    Exito: sella verificado. Fallo: 401/429 con intentos/bloqueo."""
    tipo, referencia = "PERSONA", codigo
    reg = repo.obtener(db, tipo, referencia)
    _exigir_no_bloqueado(reg)
    ok = bool(dni_real) and (dni_ingresado or "").strip() == dni_real.strip()[-4:]
    if not ok:
        _aplicar_fallo(db, reg, tipo, referencia, bloqueo_seg=BLOQUEO_DNI_SEG)
    repo.upsert(db, tipo, referencia, intentos=0, bloqueos=0, bloqueado_hasta=None, canal="DNI", verificado_en=datetime.utcnow())
    repo.guardar(db)


def emitir_otp(db: Session, tipo: str, referencia: str) -> str:
    """Genera y persiste (hasheado) un OTP con 10 min de vigencia; devuelve el OTP en claro.
    Recibe tipo (PERSONA|EMPRESA) y referencia. Un reenvio durante un bloqueo activo
    NO lo levanta (evita que reenviar el codigo burle el bloqueo por intentos)."""
    reg = repo.obtener(db, tipo, referencia)
    _exigir_no_bloqueado(reg)
    otp = gen_otp()
    repo.upsert(
        db, tipo, referencia,
        canal="OTP_CORREO",
        codigo_hash=get_password_hash(otp),
        expira_en=datetime.utcnow() + timedelta(minutes=10),
        intentos=0,
        bloqueado_hasta=None,
    )
    repo.guardar(db)
    return otp


def verificar_otp(db: Session, tipo: str, referencia: str, otp_ingresado: str | None, bloqueo_seg: int = BLOQUEO_OTP_SEG) -> None:
    """Valida el OTP contra el hash vigente + expiracion + intentos. Recibe tipo, referencia y OTP.
    Exito: sella verificado e invalida el codigo. Fallo: 401/429."""
    reg = repo.obtener(db, tipo, referencia)
    _exigir_no_bloqueado(reg)
    vigente = bool(reg and reg.codigo_hash and reg.expira_en and reg.expira_en > datetime.utcnow())
    ok = vigente and verify_password((otp_ingresado or "").strip(), reg.codigo_hash)
    if not ok:
        _aplicar_fallo(db, reg, tipo, referencia, bloqueo_seg=bloqueo_seg)
    # El codigo es de un solo uso (C44-01): se borra al usarlo para que no sirva otra vez.
    repo.upsert(db, tipo, referencia, intentos=0, bloqueos=0, bloqueado_hasta=None,
                codigo_hash=None, expira_en=None, verificado_en=datetime.utcnow())
    repo.guardar(db)
