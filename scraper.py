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
ABOUT_PATHS = ["/about", "/about-us", "/team", "/о-компании", "/команда", "/about-company"]
REQUEST_TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def extract_email(html: str) -> str:
    """Извлекает email из HTML. Приоритет: info@ > sales@ > hello@ > contact@ > любой."""
    emails = EMAIL_REGEX.findall(html)
    emails = [e for e in emails if not any(skip in e for skip in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", "example.com"])]
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
                    words = candidate.split()
                    if (re.match(r'^[А-ЯЁA-Z][а-яёa-z\-]+ [А-ЯЁA-Z][а-яёa-z\-]+', candidate)
                            and len(candidate) < 50
                            and len(words) <= 4
                            and not re.search(r'\d', candidate)):
                        return candidate, line
    return "", ""


def load_processed(contacts_path: str) -> set:
    """Загружает уже обработанные компании из contacts.csv для чекпоинтинга."""
    processed = set()
    if not Path(contacts_path).exists():
        return processed
    with open(contacts_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            processed.add(row.get("Компания", ""))
    return processed


def scrape_company(name: str, url: str, session: requests.Session) -> dict:
    """Обходит сайт компании, извлекает email и данные ЛПР."""
    result = {
        "Компания": name,
        "Сайт": url,
        "Email": "",
        "Имя_ЛПР": "",
        "Должность": "",
        "Статус": "не найдено",
    }
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        html = resp.text
        result["Email"] = extract_email(html)
        result["Имя_ЛПР"], result["Должность"] = find_lpr(html)

        if not result["Имя_ЛПР"]:
            base = url.rstrip("/")
            for path in ABOUT_PATHS:
                try:
                    r = session.get(base + path, timeout=REQUEST_TIMEOUT, headers=HEADERS)
                    if r.status_code == 200:
                        lpr_name, lpr_title = find_lpr(r.text)
                        if lpr_name:
                            result["Имя_ЛПР"] = lpr_name
                            result["Должность"] = lpr_title
                            if not result["Email"]:
                                result["Email"] = extract_email(r.text)
                            break
                        time.sleep(random.uniform(0.5, 1.0))
                except Exception:
                    continue

        result["Статус"] = "ok"
    except requests.exceptions.RequestException:
        result["Статус"] = "ошибка"
    except Exception:
        result["Статус"] = "ошибка"
    return result


def main():
    companies_file = "companies.csv"
    contacts_file = "contacts.csv"

    with open(companies_file, encoding="utf-8", newline="") as f:
        companies = [(row["Компания"], row["Сайт"]) for row in csv.DictReader(f)]

    processed = load_processed(contacts_file)
    to_process = [(n, u) for n, u in companies if n not in processed]
    print(f"Всего: {len(companies)}, обработано: {len(processed)}, осталось: {len(to_process)}")

    file_exists = Path(contacts_file).exists()
    with open(contacts_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CONTACTS_COLUMNS)
        if not file_exists:
            writer.writeheader()

        session = requests.Session()
        for name, url in tqdm(to_process, desc="Обработка компаний"):
            result = scrape_company(name, url, session)
            writer.writerow(result)
            f.flush()
            time.sleep(random.uniform(2, 3))

    print(f"\nГотово! Результаты в {contacts_file}")


if __name__ == "__main__":
    main()
