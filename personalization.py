import csv
import os
import random
import time
from pathlib import Path

from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

CONTACTS_FILE = "contacts.csv"
MODEL_NAME = "gpt-4o-mini"
MAX_TEXT_CHARS = 3000
REQUEST_TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SYSTEM_PROMPT = (
    "Ты помощник для B2B аутрича. "
    "На основе текста сайта напиши 1-2 предложения персонализации для холодного письма. "
    "Начинай сразу с конкретного факта о компании — без приветствий, без «Я заметил», без «Здравствуйте». "
    "Пример: «Kokoc Group входит в топ-5 performance-агентств России и работает с 2010 года...» "
    "Только реальные факты с сайта. Без общих фраз. На русском языке."
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


def generate_personalization(page_text: str, client: OpenAI) -> str:
    """Генерирует персонализацию через OpenAI API на основе текста сайта."""
    if not page_text.strip():
        return ""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Текст сайта:\n{page_text}"},
            ],
            timeout=30,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Ошибка API: {e}")
        return ""


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: переменная окружения OPENAI_API_KEY не установлена.")
        print('Установите: $env:OPENAI_API_KEY="ваш_ключ_здесь"')
        return

    if not Path(CONTACTS_FILE).exists():
        print(f"Файл {CONTACTS_FILE} не найден. Сначала запустите scraper.py.")
        return

    client = OpenAI(api_key=api_key)
    session = requests.Session()

    with open(CONTACTS_FILE, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "Персонализация" not in fieldnames:
        fieldnames = fieldnames + ["Персонализация"]

    for row in tqdm(rows, desc="Генерация персонализации"):
        if row.get("Персонализация"):
            continue

        url = row.get("Сайт", "")
        if not url:
            row["Персонализация"] = ""
            continue

        page_text = fetch_page_text(url, session)
        row["Персонализация"] = generate_personalization(page_text, client)
        time.sleep(random.uniform(2, 3))

    with open(CONTACTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nГотово! Персонализация добавлена в {CONTACTS_FILE}")


if __name__ == "__main__":
    main()
