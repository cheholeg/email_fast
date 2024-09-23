import email
import imaplib
import json
import logging
import os
import re
import tempfile
from datetime import datetime
from email.header import decode_header

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.models import MailAccount, MailMessage
from database import AsyncSessionLocal
from services.websocket_manager import manager
from utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

router = APIRouter()

active_fetch_processes = {}

# Функция для запуска задачи fetch_messages
async def start_fetch_messages(mail_account_id: int):
    return await fetch_messages(mail_account_id)

async def fetch_messages(mail_account_id: int):
    logger.info(f"Starting to fetch messages for account {mail_account_id}")
    async with AsyncSessionLocal() as db:
        mail_account = await db.execute(select(MailAccount).options(joinedload(MailAccount.service)).filter(MailAccount.id == mail_account_id))
        mail_account = mail_account.scalar_one_or_none()


        if not mail_account:
            await broadcast_status(mail_account_id, "error", "Аккаунт не найден")
            return

        await broadcast_status(mail_account_id, "started", f"Запущено")

        if not mail_account.service:
            return {"status": "error", "message": "Mail service not found for this account"}
        imap_server = mail_account.service.imap_server
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(mail_account.login, mail_account.password)
            mail.select("inbox")
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            total_emails = len(email_ids)
            logger.info(f"Total emails to process: {total_emails}")
            for index, email_id in enumerate(email_ids):
                logger.debug(f"Processing email {index + 1} of {total_emails}")
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                progress = int((index + 1) / total_emails * 100)
                await broadcast_progress(mail_account.id, progress, mail_account.login)

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        message_id = msg.get('Message-Id')

                        # Пропускаем уже существующие сообщения
                        existing_message = await db.execute(
                            select(MailMessage).filter(MailMessage.message_id == message_id))
                        if existing_message.scalar_one_or_none():
                            continue

                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else 'utf-8')

                        send_date = msg.get("Date")
                        try:
                            date_object = parsedate_to_datetime(send_date)
                        except (TypeError, ValueError):
                            # If that fails, fall back to a more manual parsing method
                            try:
                                # Remove any parenthetical content at the end of the string
                                send_date = re.sub(r'\([^)]*\)$', '', send_date).strip()

                                # List of date formats to try
                                date_formats = [
                                    "%a, %d %b %Y %H:%M:%S %z",
                                    "%d %b %Y %H:%M:%S %z",
                                    "%a, %d %b %Y %H:%M:%S",
                                    "%d %b %Y %H:%M:%S"
                                ]

                                for date_format in date_formats:
                                    try:
                                        date_object = datetime.strptime(send_date, date_format)
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    # If none of the formats work, raise an exception
                                    raise ValueError(f"Unable to parse date string: {send_date}")
                            except Exception as e:
                                # If all parsing attempts fail, log the error and use current time
                                logger.error(f"Error parsing date '{send_date}': {str(e)}")
                                date_object = datetime.now()

                        if msg.is_multipart():
                            text = ""
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    text = part.get_payload(decode=True).decode()
                        else:
                            text = msg.get_payload(decode=True).decode()

                        mail_message = MailMessage(
                            message_id=message_id,
                            mail_account_id=mail_account.id,
                            subject=subject or 'No subject',
                            send_date=date_object,
                            receive_date=datetime.now(),
                            text=text
                        )

                        files = []
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_disposition = str(part.get("Content-Disposition"))
                                if "attachment" in content_disposition:
                                    filename = part.get_filename()
                                    decoded_header = decode_header(filename)
                                    filename = ''.join(
                                        str(text, encoding if encoding else 'utf-8') for text, encoding in
                                        decoded_header)
                                    if filename:
                                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                                            temp_file.write(part.get_payload(decode=True))
                                            temp_file.flush()
                                            files.append(filename)
                                        os.remove(temp_file.name)

                        mail_message.files = ', '.join(files) if files else None
                        db.add(mail_message)

                await db.commit()
            await broadcast_status(mail_account_id, "completed",
                                       f"Завершено")
            mail.logout()
            return {"status": "success", "message": "Messages fetched successfully"}
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            if mail_account_id in active_fetch_processes:
                del active_fetch_processes[mail_account_id]

async def broadcast_progress(account_id: int, progress: int, account_name: str):
    logger.debug(f"Broadcasting progress: account_id={account_id}, progress={progress}")
    await manager.broadcast(json.dumps({
        "type": "send_progress",
        "account_id": account_id,
        "progress": progress,
        "account_name": account_name
    }))

async def broadcast_status(account_id: int, status: str, message: str):
    await manager.broadcast(json.dumps({
        "type": "fetch_status",
        "account_id": account_id,
        "status": status,
        "message": message
    }))
