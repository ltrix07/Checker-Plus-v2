import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_item_title_valid(valid_html):
    parser = EbayParser(valid_html)
    title = await parser.get_item_title()
    assert title == "Test Item"


@pytest.mark.asyncio
async def test_get_item_title_empty(empty_html):
    parser = EbayParser(empty_html)
    title = await parser.get_item_title()
    assert title is None
