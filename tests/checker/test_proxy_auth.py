import pytest
from checker_plus.checker import Checker
from aiohttp import BasicAuth


@pytest.mark.asyncio
@pytest.mark.parametrize("proxies_list, expect_result", [
    (
        ["skotarenko138:pTphNcpBUQ@161.77.65.33:59100", "skotarenko138:pTphNcpBUQ@161.77.55.241:59100"],
        [
            dict(url="http://161.77.65.33:59100", auth=BasicAuth("skotarenko138", "pTphNcpBUQ")),
            dict(url="http://161.77.55.241:59100", auth=BasicAuth("skotarenko138", "pTphNcpBUQ"))
        ]
    ),
    (
        ["test:test@161.77.65.33:59100", "test:test@161.77.55.241:59100"],
        [
            dict(url="http://161.77.65.33:59100", auth=BasicAuth("test", "test")),
            dict(url="http://161.77.55.241:59100", auth=BasicAuth("test", "test"))
        ]
    )
])
async def test_proxy_auth(proxies_list, expect_result):
    checker = Checker({}, proxies_list, [], {}, [], [])
    await checker.proxy_auth()
    assert checker.auth_proxies == expect_result


@pytest.mark.asyncio
@pytest.mark.parametrize("proxies_list, expect_error", [
    (["skotarenko138:pTphNcpBUQ:161.77.65.33:59100", "skotarenko138:pTphNcpBUQ:161.77.55.241:59100"], TypeError),
    (["skotarenko138pTphNcpBUQ161.77.65.3359100", "skotarenko138:pTphNcpBUQ:161.77.55.241:59100"], TypeError)
])
async def test_proxy_auth_errors(proxies_list, expect_error):
    checker = Checker({}, proxies_list, [], {}, [], [])
    with pytest.raises(expect_error):
        await checker.proxy_auth()
