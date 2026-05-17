from unittest.mock import MagicMock
import pytest
from personalization import generate_personalization, fetch_page_text


def test_generate_personalization_returns_text():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        'Компания разрабатывает CRM-системы для малого бизнеса.'
    )

    result = generate_personalization('Текст сайта компании', mock_client)

    assert result == 'Компания разрабатывает CRM-системы для малого бизнеса.'
    mock_client.chat.completions.create.assert_called_once()


def test_generate_personalization_handles_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception('API Error')

    result = generate_personalization('Текст сайта', mock_client)

    assert result == ''


def test_generate_personalization_returns_empty_for_blank_text():
    mock_client = MagicMock()

    result = generate_personalization('   ', mock_client)

    assert result == ''
    mock_client.chat.completions.create.assert_not_called()


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
