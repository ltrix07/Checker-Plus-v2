import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_price_valid(valid_html):
    parser = EbayParser(valid_html)
    price = await parser.get_price()
    assert price == "43.54"


@pytest.mark.asyncio
async def test_get_price_empty(empty_html):
    parser = EbayParser(empty_html)
    price = await parser.get_price()
    assert price is None
