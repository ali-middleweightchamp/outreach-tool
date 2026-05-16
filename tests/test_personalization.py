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
