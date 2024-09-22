from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session

from core.models import MailAccount, MailService
from core.schemas import MailAccountCreate, DeleteAccountRequest
from database import get_db, templates
from utils import get_username_regex

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    mail_accounts = db.query(MailAccount).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "mail_accounts": mail_accounts
        }
    )

@router.get("/create_login/", response_class=HTMLResponse)
async def create_account_form(
    request: Request,
    db: Session = Depends(get_db)
):
    services = db.query(MailService).all()
    return templates.TemplateResponse(
        "create_account.html",
        {
            "request": request,
            "services": services
        }
    )

@router.post("/create_login/")
def create_account(
    request: Request,
    account_data: MailAccountCreate,
    db: Session = Depends(get_db)
):
    email = get_username_regex(account_data.email)
    existing_user = db.query(MailAccount).filter(MailAccount.login == email).first()
    if existing_user:
        return templates.TemplateResponse(
            "create_account.html", {
                "request": request,
                "error": "Email уже зарегистрирован"
            }
        )


    service = db.query(MailService).filter(MailService.name == account_data.service_name).first()
    if not service:
        return templates.TemplateResponse("create_account.html", {
            "request": request,
            "error": "Указанный сервис не найден"
        })

    new_mail_account = MailAccount(
        service_id=service.id,
        login=email,
        password=account_data.password
    )
    db.add(new_mail_account)
    db.commit()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "success": "Аккаунт успешно создан"
    })

@router.post("/delete_login/")
async def delete_account(
        request: DeleteAccountRequest,
        db: Session = Depends(get_db)
):
    user = db.query(MailAccount).filter(MailAccount.id == request.account_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учетная запись не найдена")

    db.delete(user)
    db.commit()

    return JSONResponse(content={"message": "Учетная запись успешно удалена"})
