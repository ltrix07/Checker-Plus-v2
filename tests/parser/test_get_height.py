import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_height_valid(valid_html):
    parser = EbayParser(valid_html)
    height = await parser.get_height()
    assert height == "test height"


@pytest.mark.asyncio
async def test_get_height_empty(empty_html):
    parser = EbayParser(empty_html)
    height = await parser.get_height()
    assert height is None
