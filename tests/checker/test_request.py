import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from checker_plus.checker import Checker
from aiohttp import client_exceptions, ClientRequest


@pytest.mark.asyncio
async def test_request_success():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    response_mock = MagicMock()
    response_mock.status = 200
    response_mock.text = AsyncMock(return_value="<html>Response 200</html>")

    mock_session_get = MagicMock()
    mock_session_get.__aenter__.return_value = response_mock
    mock_session_get.__aexit__.return_value = AsyncMock()

    with patch("aiohttp.ClientSession.get", return_value=mock_session_get):
        result = await checker.request(link, proxy)
        assert result == "<html>Response 200</html>"


@pytest.mark.asyncio
async def test_request_400_error():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    response_mock = MagicMock()
    response_mock.status = 400

    mock_session_get = MagicMock()
    mock_session_get.__aenter__.return_value = response_mock
    mock_session_get.__aexit__.return_value = AsyncMock()

    with patch("aiohttp.ClientSession.get", return_value=mock_session_get):
        result = await checker.request(link, proxy)
        assert result == "{400_bad_request}"


@pytest.mark.asyncio
async def test_request_404_error():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    response_mock = MagicMock()
    response_mock.status = 404

    mock_session_get = MagicMock()
    mock_session_get.__aenter__.return_value = response_mock
    mock_session_get.__aexit__.return_value = AsyncMock()

    with patch("aiohttp.ClientSession.get", return_value=mock_session_get):
        result = await checker.request(link, proxy)
        assert result == "{404}"


@pytest.mark.asyncio
async def test_request_403_error():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    response_mock = MagicMock()
    response_mock.status = 403

    mock_session_get = MagicMock()
    mock_session_get.__aenter__.return_value = response_mock
    mock_session_get.__aexit__.return_value = AsyncMock()

    with patch("aiohttp.ClientSession.get", return_value=mock_session_get):
        result = await checker.request(link, proxy)
        assert result == "{website_close_connection}"


@pytest.mark.asyncio
async def test_request_proxy_error():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    # Создаем объект OSError для side_effect
    os_error = OSError(111, "Connection refused")

    with patch("aiohttp.ClientSession.get", side_effect=client_exceptions.ClientProxyConnectionError(connection_key=None, os_error=os_error)):
        result = await checker.request(link, proxy)
        assert result == "{proxy_error}"

    with patch("aiohttp.ClientSession.get", side_effect=client_exceptions.ClientConnectorError(connection_key=None, os_error=os_error)):
        result = await checker.request(link, proxy)
        assert result == "{proxy_error}"

    # Убираем аргументы для ClientOSError
    with patch("aiohttp.ClientSession.get", side_effect=client_exceptions.ClientOSError):
        result = await checker.request(link, proxy)
        assert result == "{proxy_error}"


@pytest.mark.asyncio
async def test_request_content_type_error():
    checker = Checker({}, [], [], {}, [], [])
    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    # Убираем использование ClientRequestInfo и передаем параметры напрямую
    with patch("aiohttp.ClientSession.get", side_effect=client_exceptions.ContentTypeError(request_info=None, history=None)):
        result = await checker.request(link, proxy)
        assert result == "{400_bad_request}"


@pytest.mark.asyncio
async def test_request_client_response_error():
    checker = Checker({}, [], [], {}, [], [])
    checker.report["errors"]["website_close_connection"] = 0  # инициализация ключа

    link = "https://exemple.com"
    proxy = dict(url="http://0.0.0.0:8080", auth=None)

    with patch("aiohttp.ClientSession.get", side_effect=client_exceptions.ClientResponseError(request_info=None, history=None)):
        result = await checker.request(link, proxy)
        assert result == "{website_close_connection}"
