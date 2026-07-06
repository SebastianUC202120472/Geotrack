from pydantic import BaseModel


class VerificarDni(BaseModel):
    dni: str


class Reprogramar(BaseModel):
    franja: str


class EmpresaLogin(BaseModel):
    codigoAcceso: str
    clave: str


class EmpresaVerificar(BaseModel):
    codigoAcceso: str
    otp: str


class ContactoIn(BaseModel):
    nombre: str
    empresa: str | None = None
    email: str
    telefono: str | None = None
    volumen: int | None = None
    mensaje: str | None = None
    hp: str | None = None       # honeypot: debe llegar vacio


class ReclamoConsumidor(BaseModel):
    nombre: str
    dni: str | None = None
    domicilio: str | None = None
    email: str | None = None
    telefono: str | None = None
    esMenor: bool = False


class ReclamoBien(BaseModel):
    tipo: str | None = None      # PRODUCTO | SERVICIO
    descripcion: str | None = None
    monto: float | None = None


class ReclamoIn(BaseModel):
    tipo: str                    # RECLAMO | QUEJA
    consumidor: ReclamoConsumidor
    bien: ReclamoBien | None = None
    detalle: str
    pedido: str | None = None
    hp: str | None = None
