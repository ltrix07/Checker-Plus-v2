import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_length_valid(valid_html):
    parser = EbayParser(valid_html)
    length = await parser.get_length()
    assert length == "test length"


@pytest.mark.asyncio
async def test_get_length_empty(empty_html):
    parser = EbayParser(empty_html)
    length = await parser.get_length()
    assert length is None
