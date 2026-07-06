import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.repositories import verificacion_repository as repo

LIMITE_INTENTOS = 3


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
    """Suma un intento y bloquea si toca; lanza 401/429. Recibe reto, tipo, referencia y bloqueo."""
    previos = reg.intentos if reg else 0
    r = evaluar_intento(previos, exito=False, limite=LIMITE_INTENTOS, bloqueo_seg=bloqueo_seg)
    if r["bloquear"]:
        repo.upsert(db, tipo, referencia, intentos=0, bloqueado_hasta=datetime.utcnow() + timedelta(seconds=bloqueo_seg))
        repo.guardar(db)
        raise HTTPException(status_code=429, detail={"bloqueadoSegundos": bloqueo_seg})
    repo.upsert(db, tipo, referencia, intentos=previos + 1)
    repo.guardar(db)
    raise HTTPException(status_code=401, detail={"intentosRestantes": r["intentos_restantes"]})


def verificar_dni(db: Session, codigo: str, dni_ingresado: str, dni_real: str | None) -> None:
    """Valida los ultimos 4 del DNI contra el pedido. Recibe codigo, dni ingresado y dni real (o None).
    Exito: sella verificado. Fallo: 401/429 con intentos/bloqueo."""
    tipo, referencia = "PERSONA", codigo
    reg = repo.obtener(db, tipo, referencia)
    _exigir_no_bloqueado(reg)
    ok = bool(dni_real) and (dni_ingresado or "").strip() == dni_real.strip()[-4:]
    if not ok:
        _aplicar_fallo(db, reg, tipo, referencia, bloqueo_seg=30)
    repo.upsert(db, tipo, referencia, intentos=0, bloqueado_hasta=None, canal="DNI", verificado_en=datetime.utcnow())
    repo.guardar(db)


def emitir_otp(db: Session, tipo: str, referencia: str) -> str:
    """Genera y persiste (hasheado) un OTP con 10 min de vigencia; devuelve el OTP en claro.
    Recibe tipo (PERSONA|EMPRESA) y referencia."""
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


def verificar_otp(db: Session, tipo: str, referencia: str, otp_ingresado: str, bloqueo_seg: int = 45) -> None:
    """Valida el OTP contra el hash vigente + expiracion + intentos. Recibe tipo, referencia y OTP.
    Exito: sella verificado. Fallo: 401/429."""
    reg = repo.obtener(db, tipo, referencia)
    _exigir_no_bloqueado(reg)
    vigente = bool(reg and reg.codigo_hash and reg.expira_en and reg.expira_en > datetime.utcnow())
    ok = vigente and verify_password((otp_ingresado or "").strip(), reg.codigo_hash)
    if not ok:
        _aplicar_fallo(db, reg, tipo, referencia, bloqueo_seg=bloqueo_seg)
    repo.upsert(db, tipo, referencia, intentos=0, bloqueado_hasta=None, verificado_en=datetime.utcnow())
    repo.guardar(db)
