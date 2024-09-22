import re
from datetime import datetime

def parsedate_to_datetime(send_date: str, date_format: str = "%a, %d %b %Y %H:%M:%S %z"):
    return datetime.strptime(send_date, date_format)

def datetimeformat(value: datetime, date_format: str ='%d.%m.%Y'):
    return value.strftime(date_format)

def get_username_regex(email):
    """
    Извлекает имя пользователя (часть до @) из email-адреса используя регулярное выражение.

    :param email: Полный email-адрес
    :return: Имя пользователя (часть до @)
    """
    match = re.match(r'^([^@]+)@', email)
    if match:
        return match.group(1)
    return None
