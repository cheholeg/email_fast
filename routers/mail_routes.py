from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.requests import Request

from core.models import MailMessage, MailAccount
from core.schemas import MailMessageRequest
from database import get_db, templates, get_async_db
from services.mail_service import start_fetch_messages, active_fetch_processes

router = APIRouter()


def get_page_range(current_page: int, total_pages: int) -> list[int]:
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    if current_page <= 4:
        return [1, 2, 3, 4, 5, None, total_pages]

    if current_page >= total_pages - 3:
        return [1, None, total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]

    return [1, None, current_page - 1, current_page, current_page + 1, None, total_pages]

@router.get("/messages/", response_class=HTMLResponse)
def get_messages(request: Request, mail_request: MailMessageRequest = Depends(), db: Session = Depends(get_db)):
    # Calculate offset
    offset = (mail_request.page - 1) * mail_request.per_page

    # Query for paginated messages
    messages = db.query(MailMessage).filter(MailMessage.mail_account_id == mail_request.account_id).order_by(
        MailMessage.receive_date.desc()
    ).offset(offset).limit(mail_request.per_page).all()

    # Get total count of messages
    total_messages = db.query(func.count(MailMessage.id)).filter(
        MailMessage.mail_account_id == mail_request.account_id
    ).scalar()
    total_pages = (total_messages + mail_request.per_page - 1) // mail_request.per_page

    # Get page range for pagination
    page_range = get_page_range(mail_request.page, total_pages)

    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "messages": messages,
            "page": mail_request.page,
            "per_page": mail_request.per_page,
            "total_pages": total_pages,
            "total_messages": total_messages,
            "account_id": mail_request.account_id,
            "page_range": page_range,
            "start_index": offset + 1,
        }
    )

@router.get("/fetch_messages/")
async def fetch_messages(account_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_async_db)):
    if account_id in active_fetch_processes:
        return {"status": "error", "message": "Получение почты уже выполняется для этого аккаунта"}
    mail_account = await db.get(MailAccount, account_id)
    if not mail_account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Запускаем задачу в фоновом режиме
    background_tasks.add_task(start_fetch_messages, account_id)

    return JSONResponse(content={"message": "Запущен процесс получения сообщений"})
