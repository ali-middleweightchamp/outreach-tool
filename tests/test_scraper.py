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
