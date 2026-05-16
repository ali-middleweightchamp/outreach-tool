import csv
import os
import random
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

PRIORITY_PREFIXES = ("info@", "sales@", "hello@", "contact@")
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
CONTACTS_COLUMNS = ["Компания", "Сайт", "Email", "Имя_ЛПР", "Должность", "Статус"]
ABOUT_PATHS = ["/about", "/about-us", "/team", "/о-компания", "/команда", "/about-company"]
REQUEST_TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def extract_email(html: str) -> str:
    """Извлекает email из HTML. Приоритет: info@ > sales@ > hello@ > contact@ > любой."""
    emails = EMAIL_REGEX.findall(html)
    emails = [e for e in emails if not any(skip in e for skip in [".png", ".jpg", ".gif", "example.com"])]
    for prefix in PRIORITY_PREFIXES:  # Перебираем приоритеты по порядку
        for email in emails:
            if email.lower().startswith(prefix):
                return email
    return emails[0] if emails else ""
