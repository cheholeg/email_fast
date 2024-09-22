from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from core.models import MailService
from core.schemas import MailServiceCreate
from database import get_db

router = APIRouter()

@router.post("/create_service/")
async def create_service(
    service_data: MailServiceCreate,
    db: Session = Depends(get_db)
):
    existing_service = db.query(MailService).filter(MailService.name == service_data.name).first()
    if existing_service:
        return JSONResponse(
            status_code=400,
            content={"error": "Сервис с таким названием уже существует"}
        )

    new_service = MailService(
        name=service_data.name,
        imap_server=service_data.imap_server,
        is_custom=True
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return RedirectResponse(url="/", status_code=100)
