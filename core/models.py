from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Model


class MailService(Model):
    __tablename__ = "mail_services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    imap_server: Mapped[str] = mapped_column(String)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    mail_accounts: Mapped[list["MailAccount"]] = relationship(back_populates="service")

class MailAccount(Model):
    __tablename__ = "mail_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("mail_services.id"), index=True)
    login: Mapped[str] = mapped_column(String, index=True)
    password: Mapped[str] = mapped_column(String)

    service: Mapped["MailService"] = relationship(back_populates="mail_accounts")
    messages: Mapped[list["MailMessage"]] = relationship(back_populates="mail_account")

class MailMessage(Model):
    __tablename__ = "mail_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    mail_account_id: Mapped[int] = mapped_column(ForeignKey("mail_accounts.id"))
    subject: Mapped[str] = mapped_column(String)
    send_date: Mapped[datetime] = mapped_column(DateTime)
    receive_date: Mapped[datetime] = mapped_column(DateTime)
    text: Mapped[str] = mapped_column(String)
    files: Mapped[str | None] = mapped_column(String, nullable=True)

    mail_account: Mapped["MailAccount"] = relationship(back_populates="messages")