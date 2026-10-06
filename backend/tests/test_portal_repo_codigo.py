import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.pedido import Pedido
from app.repositories.portal_repository import pedido_por_codigo


@pytest.fixture()
def db():
    """Sesion contra una base SQLite en memoria con la tabla de pedidos creada. Sin input."""
    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor, tables=[Pedido.__table__])
    sesion = sessionmaker(bind=motor)()
    sesion.add_all([
        Pedido(codigo="PD-014", referencia_externa="RPL-1000",
               cliente_origen="Ripley S.A.", direccion_destino="Av. Larco 137, Miraflores, Lima, Peru"),
        Pedido(codigo="PD-015", referencia_externa="RPL-1001",
               cliente_origen="Ripley S.A.", direccion_destino="Av. Pardo 174, Miraflores, Lima, Peru"),
    ])
    sesion.commit()
    yield sesion
    sesion.close()


def test_encuentra_por_codigo_interno(db):
    assert pedido_por_codigo(db, "PD-014").referencia_externa == "RPL-1000"


def test_encuentra_por_referencia_del_retail(db):
    """El destinatario conoce el numero de la tienda, no el codigo interno de SAVA."""
    assert pedido_por_codigo(db, "RPL-1001").codigo == "PD-015"


def test_codigo_inexistente_devuelve_none(db):
    assert pedido_por_codigo(db, "PD-999") is None
    assert pedido_por_codigo(db, "") is None
