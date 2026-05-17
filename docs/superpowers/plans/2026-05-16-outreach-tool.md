# B2B Outreach Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать систему из двух Python-скриптов для обогащения базы B2B компаний контактами (scraper.py) и персонализацией через Claude API (personalization.py).

**Architecture:** Два независимых последовательных скрипта. `scraper.py` читает `companies.csv`, обходит сайты и пишет `contacts.csv` с чекпоинтингом. `personalization.py` читает `contacts.csv`, вызывает Claude API и добавляет колонку «Персонализация».

**Tech Stack:** Python 3.9+, requests, beautifulsoup4, tqdm, anthropic SDK, pytest

---

## Структура файлов

```
outreach-tool/
├── companies.csv              # Входная база (создаётся в Task 1)
├── contacts.csv               # Генерируется scraper.py
├── scraper.py                 # Task 4
├── personalization.py         # Task 5–6
├── requirements.txt           # Task 1
├── README.md                  # Task 7
└── tests/
    ├── test_scraper.py        # Tasks 2–3
    └── test_personalization.py # Task 5
```

---

## Task 1: Базовая настройка — requirements.txt и companies.csv

**Files:**
- Create: `C:\Users\user\Desktop\outreach-tool\requirements.txt`
- Create: `C:\Users\user\Desktop\outreach-tool\companies.csv`

- [ ] **Step 1: Создать requirements.txt**

```
requests==2.32.3
beautifulsoup4==4.12.3
tqdm==4.67.1
anthropic==0.52.0
pytest==8.3.5
```

- [ ] **Step 2: Создать companies.csv с примером данных**

Создать файл `companies.csv` (заменить примеры на реальные компании):

```csv
Компания,Сайт
Пример Компания 1,https://example.com
Пример Компания 2,https://example.org
```

> Пользователь заполняет этот файл своими компаниями перед запуском.

- [ ] **Step 3: Установить зависимости**

```bash
cd C:\Users\user\Desktop\outreach-tool
pip install -r requirements.txt
```

Ожидаемый результат: все пакеты установлены без ошибок.

- [ ] **Step 4: Commit**

```bash
git init
git add requirements.txt companies.csv
git commit -m "feat: project setup — requirements and sample companies"
```

---

## Task 2: Функция извлечения email — TDD

**Files:**
- Create: `C:\Users\user\Desktop\outreach-tool\tests/test_scraper.py`
- Create: `C:\Users\user\Desktop\outreach-tool\scraper.py` (только функция `extract_email`)

- [ ] **Step 1: Написать падающие тесты**

Создать `tests/test_scraper.py`:

```python
import pytest
from scraper import extract_email


def test_extract_email_prefers_info():
    html = 'Напишите нам: sales@acme.com или info@acme.com'
    assert extract_email(html) == 'info@acme.com'


def test_extract_email_prefers_sales_over_generic():
    html = 'Контакты: admin@acme.com, sales@acme.com'
    assert extract_email(html) == 'sales@acme.com'


def test_extract_email_falls_back_to_any():
    html = 'Пишите: support@acme.com'
    assert extract_email(html) == 'support@acme.com'


def test_extract_email_returns_empty_if_none():
    html = '<p>Нет email на этой странице</p>'
    assert extract_email(html) == ''


def test_extract_email_ignores_image_paths():
    html = 'img src="photo.png" alt="photo@2x.jpg" contact: info@acme.com'
    assert extract_email(html) == 'info@acme.com'
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
python -m pytest tests/test_scraper.py -v
```

Ожидаемый результат: `ERROR` — `ModuleNotFoundError: No module named 'scraper'`

- [ ] **Step 3: Создать scraper.py с функцией extract_email**

Создать `scraper.py`:

```python
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
    emails = [e for e in emails if not any(skip in e for skip in [".png", ".jpg", ".gif", "example.com"])]
    for prefix in PRIORITY_PREFIXES:  # Перебираем приоритеты по порядку
        for email in emails:
            if email.lower().startswith(prefix):
                return email
    return emails[0] if emails else ""
```

- [ ] **Step 4: Запустить тесты — убедиться, что они проходят**

```bash
python -m pytest tests/test_scraper.py -v
```

Ожидаемый результат: все 5 тестов `PASSED`

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add extract_email with priority prefix logic"
```

---

## Task 3: Функция поиска ЛПР — TDD

**Files:**
- Modify: `C:\Users\user\Desktop\outreach-tool\scraper.py` (добавить `find_lpr`)
- Modify: `C:\Users\user\Desktop\outreach-tool\tests/test_scraper.py` (добавить тесты)

- [ ] **Step 1: Добавить падающие тесты в test_scraper.py**

Дописать в конец `tests/test_scraper.py`:

```python
from scraper import find_lpr


def test_find_lpr_extracts_english_ceo():
    html = '<div><h3>Ivan Ivanov</h3><p>CEO</p></div>'
    name, title = find_lpr(html)
    assert name == 'Ivan Ivanov'
    assert 'CEO' in title


def test_find_lpr_extracts_russian_director():
    html = '<div><p>Директор</p><h3>Иван Иванов</h3></div>'
    name, title = find_lpr(html)
    assert name == 'Иван Иванов'
    assert 'Директор' in title


def test_find_lpr_returns_empty_if_none():
    html = '<p>О нашей компании. Мы делаем продукты.</p>'
    name, title = find_lpr(html)
    assert name == ''
    assert title == ''


def test_find_lpr_ignores_short_words():
    html = '<p>CEO</p><p>Он основал компанию.</p>'
    name, title = find_lpr(html)
    assert name == ''
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
python -m pytest tests/test_scraper.py::test_find_lpr_extracts_english_ceo -v
```

Ожидаемый результат: `ERROR` — `ImportError: cannot import name 'find_lpr'`

- [ ] **Step 3: Добавить find_lpr в scraper.py**

Добавить после функции `extract_email`:

```python
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
                    # Имя: два слова с заглавной буквы, длина до 50 символов
                    if re.match(r'^[А-ЯЁA-Z][а-яёa-z\-]+ [А-ЯЁA-Z][а-яёa-z\-]+', candidate) and len(candidate) < 50:
                        return candidate, line
    return "", ""
```

- [ ] **Step 4: Запустить все тесты**

```bash
python -m pytest tests/test_scraper.py -v
```

Ожидаемый результат: все 9 тестов `PASSED`

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add find_lpr with title-proximity matching"
```

---

## Task 4: scraper.py — основной цикл с чекпоинтингом

**Files:**
- Modify: `C:\Users\user\Desktop\outreach-tool\scraper.py` (добавить `load_processed`, `scrape_company`, `main`)

- [ ] **Step 1: Добавить load_processed в scraper.py**

Добавить после `find_lpr`:

```python
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
```

- [ ] **Step 2: Добавить scrape_company в scraper.py**

Добавить после `load_processed`:

```python
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
```

- [ ] **Step 3: Добавить main() в scraper.py**

Добавить в конец файла:

```python
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
```

- [ ] **Step 4: Проверить, что все тесты по-прежнему проходят**

```bash
python -m pytest tests/test_scraper.py -v
```

Ожидаемый результат: все 9 тестов `PASSED`

- [ ] **Step 5: Commit**

```bash
git add scraper.py
git commit -m "feat: add scraper main loop with checkpointing and tqdm progress"
```

---

## Task 5: personalization.py с тестами — TDD

**Files:**
- Create: `C:\Users\user\Desktop\outreach-tool\tests/test_personalization.py`
- Create: `C:\Users\user\Desktop\outreach-tool\personalization.py`

- [ ] **Step 1: Написать падающие тесты**

Создать `tests/test_personalization.py`:

```python
from unittest.mock import MagicMock, patch
import pytest
from personalization import generate_personalization, fetch_page_text


def test_generate_personalization_returns_text():
    mock_client = MagicMock()
    mock_content = MagicMock()
    mock_content.text = 'Компания разрабатывает CRM-системы для малого бизнеса.'
    mock_client.messages.create.return_value.content = [mock_content]

    result = generate_personalization('Текст сайта компании', mock_client)

    assert result == 'Компания разрабатывает CRM-системы для малого бизнеса.'
    mock_client.messages.create.assert_called_once()


def test_generate_personalization_handles_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception('API Error')

    result = generate_personalization('Текст сайта', mock_client)

    assert result == ''


def test_generate_personalization_returns_empty_for_blank_text():
    mock_client = MagicMock()

    result = generate_personalization('   ', mock_client)

    assert result == ''
    mock_client.messages.create.assert_not_called()


def test_fetch_page_text_truncates_to_3000_chars():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '<p>' + 'A' * 10000 + '</p>'
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    result = fetch_page_text('https://example.com', mock_session)

    assert len(result) <= 3000


def test_fetch_page_text_returns_empty_on_error():
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception('Connection refused')

    result = fetch_page_text('https://example.com', mock_session)

    assert result == ''
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
python -m pytest tests/test_personalization.py -v
```

Ожидаемый результат: `ERROR` — `ModuleNotFoundError: No module named 'personalization'`

- [ ] **Step 3: Создать personalization.py с функциями generate_personalization и fetch_page_text**

Создать `personalization.py`:

```python
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
```

- [ ] **Step 4: Запустить все тесты**

```bash
python -m pytest tests/ -v
```

Ожидаемый результат: все 14 тестов `PASSED`

- [ ] **Step 5: Commit**

```bash
git add personalization.py tests/test_personalization.py
git commit -m "feat: add personalization functions with Claude API integration"
```

---

## Task 6: personalization.py — функция main()

**Files:**
- Modify: `C:\Users\user\Desktop\outreach-tool\personalization.py` (добавить `main`)

- [ ] **Step 1: Добавить main() в personalization.py**

Добавить в конец `personalization.py`:

```python
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Ошибка: переменная окружения ANTHROPIC_API_KEY не установлена.")
        print("Установите: set ANTHROPIC_API_KEY=ваш_ключ_здесь")
        return

    if not Path(CONTACTS_FILE).exists():
        print(f"Файл {CONTACTS_FILE} не найден. Сначала запустите scraper.py.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    session = requests.Session()

    with open(CONTACTS_FILE, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

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
```

- [ ] **Step 2: Прогнать все тесты**

```bash
python -m pytest tests/ -v
```

Ожидаемый результат: все 14 тестов `PASSED`

- [ ] **Step 3: Commit**

```bash
git add personalization.py
git commit -m "feat: add personalization main loop with checkpointing"
```

---

## Task 7: README.md

**Files:**
- Create: `C:\Users\user\Desktop\outreach-tool\README.md`

- [ ] **Step 1: Создать README.md**

```markdown
# B2B Outreach Tool

Система для обогащения базы B2B компаний контактами и персонализацией.

## Установка

```bash
pip install -r requirements.txt
```

## Шаг 1: Заполните базу компаний

Откройте `companies.csv` и добавьте свои компании:

```csv
Компания,Сайт
ООО Рога и Копыта,https://rogaikopyta.ru
Acme Corp,https://acme.com
```

## Шаг 2: Скрапинг контактов

```bash
python scraper.py
```

Скрипт обходит сайты и сохраняет результаты в `contacts.csv`.  
Можно прерывать и запускать снова — уже обработанные компании пропускаются.

## Шаг 3: Генерация персонализации

Установите API ключ Anthropic:

```bash
# Windows CMD
set ANTHROPIC_API_KEY=ваш_ключ_здесь

# Windows PowerShell
$env:ANTHROPIC_API_KEY="ваш_ключ_здесь"
```

Запустите:

```bash
python personalization.py
```

Скрипт добавит колонку «Персонализация» в `contacts.csv`.

## Структура contacts.csv

| Колонка        | Описание                              |
|----------------|---------------------------------------|
| Компания       | Название из companies.csv             |
| Сайт           | URL компании                          |
| Email          | Найденный контактный email            |
| Имя_ЛПР        | Имя лица, принимающего решения        |
| Должность      | Должность ЛПР                        |
| Статус         | ok / ошибка / не найдено             |
| Персонализация | 1-2 предложения от Claude (после шага 3) |

## Запуск тестов

```bash
python -m pytest tests/ -v
```
```

- [ ] **Step 2: Commit финальный**

```bash
git add README.md
git commit -m "docs: add README with step-by-step usage guide"
```

---

## Итоговая проверка

- [ ] Запустить все тесты: `python -m pytest tests/ -v` → 14 PASSED
- [ ] Убедиться, что `python scraper.py` стартует без ошибок (прервать через Ctrl+C после начала)
- [ ] Убедиться, что `python personalization.py` выводит понятное сообщение при отсутствии API ключа
