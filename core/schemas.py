from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class MailAccountCreate(BaseModel):
    email: EmailStr
    password: str
    service_name: str

class MailServiceCreate(BaseModel):
    name: str
    imap_server: str

class DeleteAccountRequest(BaseModel):
    account_id: int

class MailMessageRequest(BaseModel):
    account_id: int
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
