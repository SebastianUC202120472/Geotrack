import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _texto(v, minimo: int, nombre: str):
    """Limpia espacios y exige un largo minimo. Recibe el valor, el minimo y el nombre del campo."""
    v = " ".join((v or "").split())
    if len(v) < minimo:
        raise ValueError(f"{nombre}: escribe al menos {minimo} caracteres")
    return v


def _documento(v):
    """DNI (8 digitos) o carne de extranjeria: de 8 a 12 letras o numeros. Recibe el valor."""
    v = (v or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{8,12}", v):
        raise ValueError("El documento debe tener de 8 a 12 letras o números")
    return v


def _telefono(v):
    """Telefono con 7 a 15 digitos (admite +, espacios y guiones). Recibe el valor."""
    v = " ".join((v or "").split())
    if not 7 <= len(re.sub(r"\D", "", v)) <= 15 or not re.fullmatch(r"\+?[\d \-]+", v):
        raise ValueError("Escribe un teléfono válido")
    return v


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
    """Lead del formulario de contacto del landing; el correo se valida en el servidor (C39-02)."""
    nombre: str = Field(..., max_length=120)
    empresa: str | None = Field(None, max_length=120)
    email: EmailStr
    telefono: str | None = Field(None, max_length=30)
    volumen: int | None = Field(None, ge=0, le=1_000_000)
    mensaje: str | None = Field(None, max_length=2000)
    hp: str | None = None       # honeypot: debe llegar vacio

    @field_validator("nombre")
    @classmethod
    def _v_nombre(cls, v):
        return _texto(v, 2, "Nombre")


class ReclamoConsumidor(BaseModel):
    """Datos del consumidor que exige el reglamento (D.S. 011-2011-PCM, C40-01)."""
    nombre: str = Field(..., max_length=150)
    dni: str
    domicilio: str = Field(..., max_length=255)
    email: EmailStr
    telefono: str = Field(..., max_length=30)
    esMenor: bool = False
    apoderadoNombre: str | None = Field(None, max_length=150)  # padre o madre si es menor de edad
    apoderadoDni: str | None = None

    @field_validator("nombre")
    @classmethod
    def _v_nombre(cls, v):
        return _texto(v, 3, "Nombre")

    @field_validator("dni")
    @classmethod
    def _v_dni(cls, v):
        return _documento(v)

    @field_validator("domicilio")
    @classmethod
    def _v_domicilio(cls, v):
        return _texto(v, 5, "Domicilio")

    @field_validator("telefono")
    @classmethod
    def _v_telefono(cls, v):
        return _telefono(v)

    @model_validator(mode="after")
    def _v_apoderado(self):
        if self.esMenor:
            self.apoderadoNombre = _texto(self.apoderadoNombre, 3, "Nombre del padre o madre")
            self.apoderadoDni = _documento(self.apoderadoDni)
        else:
            self.apoderadoNombre = self.apoderadoDni = None
        return self


class ReclamoBien(BaseModel):
    """Bien contratado y monto reclamado."""
    tipo: str                    # PRODUCTO | SERVICIO
    descripcion: str = Field(..., max_length=500)
    monto: float | None = Field(None, ge=0, le=1_000_000)

    @field_validator("tipo")
    @classmethod
    def _v_tipo(cls, v):
        v = (v or "").strip().upper()
        if v not in ("PRODUCTO", "SERVICIO"):
            raise ValueError("El bien contratado debe ser PRODUCTO o SERVICIO")
        return v

    @field_validator("descripcion")
    @classmethod
    def _v_descripcion(cls, v):
        return _texto(v, 3, "Descripción del bien")


class ReclamoIn(BaseModel):
    """Hoja del Libro de Reclamaciones completa (C40-01)."""
    tipo: str                    # RECLAMO | QUEJA
    consumidor: ReclamoConsumidor
    bien: ReclamoBien
    detalle: str = Field(..., max_length=4000)
    pedidoConsumidor: str = Field(..., max_length=2000)  # que solicita el consumidor
    pedido: str | None = Field(None, max_length=20)
    hp: str | None = None

    @field_validator("detalle")
    @classmethod
    def _v_detalle(cls, v):
        return _texto(v, 10, "Detalle")

    @field_validator("pedidoConsumidor")
    @classmethod
    def _v_pedido_consumidor(cls, v):
        return _texto(v, 5, "Pedido del consumidor")


class ResponderReclamo(BaseModel):
    """Respuesta del proveedor al consumidor (C41-02)."""
    respuesta: str = Field(..., max_length=4000)

    @field_validator("respuesta")
    @classmethod
    def _v_respuesta(cls, v):
        return _texto(v, 10, "Respuesta")
