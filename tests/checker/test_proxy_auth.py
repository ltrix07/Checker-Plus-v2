import asyncio
from checker_plus.checker import Checker


async def test_proxy_auth():
    proxy = ""
    checker = Checker([], [], {}, [], [])
    proxy_url, proxy_auth = checker.proxy_auth()
