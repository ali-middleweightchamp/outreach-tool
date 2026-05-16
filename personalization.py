import csv
import os
import random
import time
from pathlib import Path

import anthropic
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

CONTACTS_FILE = "contacts.csv"
MODEL = "claude-sonnet-4-20250514"
MAX_TEXT_CHARS = 3000
MAX_TOKENS = 200
REQUEST_TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SYSTEM_PROMPT = (
    "Ты помощник для B2B аутрича. "
    "На основе текста сайта напиши 1-2 предложения персонализации "
    "для холодного письма. Только реальные факты с сайта. "
    "Без общих фраз. На русском языке."
)


def fetch_page_text(url: str, session: requests.Session) -> str:
    """Загружает главную страницу и возвращает чистый текст (до 3000 символов)."""
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:MAX_TEXT_CHARS]
    except Exception:
        return ""


def generate_personalization(page_text: str, client: anthropic.Anthropic) -> str:
    """Генерирует персонализацию через Claude API на основе текста сайта."""
    if not page_text.strip():
        return ""
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Текст сайта:\n{page_text}"}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  Ошибка API: {e}")
        return ""
