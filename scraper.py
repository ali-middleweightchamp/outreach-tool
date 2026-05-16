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


LPR_TITLES = [
    "ceo", "cto", "cfo", "founder", "co-founder", "director", "president",
    "head", "chief", "owner", "managing",
    "директор", "основатель", "президент", "управляющий", "генеральный",
]


def find_lpr(html: str) -> tuple:
    """Ищет имя и должность ЛПР в HTML. Возвращает (имя, должность)."""
    soup = BeautifulSoup(html, "html.parser")
    lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]

    for i, line in enumerate(lines):
        if any(title in line.lower() for title in LPR_TITLES):
            for offset in [-1, -2, 1, 2]:
                idx = i + offset
                if 0 <= idx < len(lines):
                    candidate = lines[idx]
                    # Имя: два слова с заглавной буквой, длина до 50 символов
                    if re.match(r'^[А-ЯЁA-Z][а-яёa-z\-]+ [А-ЯЁA-Z][а-яёa-z\-]+', candidate) and len(candidate) < 50:
                        return candidate, line
    return "", ""
