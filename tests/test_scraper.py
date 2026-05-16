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
