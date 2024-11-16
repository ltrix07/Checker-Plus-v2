import pytest
import asyncio
from unittest.mock import AsyncMock
from checker_plus.checker import Checker


@pytest.mark.asyncio
async def test_get_pages_empty_data():
    instance = Checker({}, [], [], {}, [], [])
    instance.logger = AsyncMock()
    instance.proxy_auth = AsyncMock()
    instance.fetch = AsyncMock(return_value={"mocked": "data"})
    instance.proxies = [{"url": "http://proxy1", "auth": None}]
    instance.auth_proxies = [{"url": "http://proxy1", "auth": None}]
    instance.headers_settings = {"user_agents": "Mozilla/5.0"}

    result = await instance.get_pages(data=[], batch_size=5)
    assert result == []


@pytest.mark.asyncio
async def test_get_pages_no_proxies():
    instance = Checker({}, [], [], {}, [], [])
    instance.logger = AsyncMock()
    instance.proxy_auth = AsyncMock()
    instance.fetch = AsyncMock()
    instance.proxies = None

    with pytest.raises(Exception, match="No proxy was specified"):
        await instance.get_pages(data=[{"key": "value"}], batch_size=5)


@pytest.mark.asyncio
async def test_get_pages_with_proxies_and_user_agents():
    instance = Checker({}, [], [], {}, [], [])
    instance.logger = AsyncMock()
    instance.proxy_auth = AsyncMock()
    instance.fetch = AsyncMock(return_value={"mocked": "data"})
    instance.proxies = [{"url": "http://proxy1", "auth": None}]
    instance.auth_proxies = [{"url": "http://proxy1", "auth": None}]
    instance.headers_settings = {"user_agents": "Mozilla/5.0"}

    data = [{"key": f"value{i}"} for i in range(10)]
    result = await instance.get_pages(data=data, batch_size=5)

    assert len(result) == 5
    assert instance.fetch.call_count == 5


@pytest.mark.asyncio
async def test_get_pages_with_batches():
    instance = Checker({}, [], [], {}, [], [])
    instance.logger = AsyncMock()
    instance.proxy_auth = AsyncMock()
    instance.fetch = AsyncMock(side_effect=[{"mocked": f"data{i}"} for i in range(10)])
    instance.proxies = [{"url": "http://proxy1", "auth": None}]
    instance.auth_proxies = [{"url": "http://proxy1", "auth": None}]
    instance.headers_settings = {"user_agents": "Mozilla/5.0"}

    data = [{"key": f"value{i}"} for i in range(10)]
    result = await instance.get_pages(data=data, batch_size=3)

    assert len(result) == 3
    assert instance.fetch.call_count == 3
