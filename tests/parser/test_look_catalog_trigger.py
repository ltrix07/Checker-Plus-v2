import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_look_catalog_trigger_valid(catalog_page):
    parser = EbayParser(catalog_page)
    await parser.look_catalog_trigger()
    assert parser.catalog_link is True


@pytest.mark.asyncio
async def test_look_catalog_trigger_empty(empty_html):
    parser = EbayParser(empty_html)
    await parser.look_catalog_trigger()
    assert parser.catalog_link is False
