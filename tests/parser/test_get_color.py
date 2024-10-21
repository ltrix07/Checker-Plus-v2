import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_color_valid(valid_html):
    parser = EbayParser(valid_html)
    color = await parser.get_color()
    assert color == "test color"


@pytest.mark.asyncio
async def test_get_color_empty(empty_html):
    parser = EbayParser(empty_html)
    color = await parser.get_color()
    assert color is None
