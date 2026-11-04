# Contactos comerciales que llegan desde el landing (C39-01). Solo admin.
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import fechas
from app.db.database import get_db
from app.api.deps import get_current_admin
from app.services import reclamo_service

router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_admin)])
def listar_contactos(db: Session = Depends(get_db)):
    """Lista los contactos comerciales, los mas recientes primero."""
    return reclamo_service.contactos(db)


@router.get("/excel", dependencies=[Depends(get_current_admin)])
def exportar_contactos(db: Session = Depends(get_db)):
    """Descarga los contactos comerciales en Excel."""
    return Response(
        content=reclamo_service.excel_contactos(db),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="contactos_{fechas.hoy_local().isoformat()}.xlsx"'},
    )
