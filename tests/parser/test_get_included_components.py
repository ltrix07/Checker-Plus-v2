import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_included_components_valid(valid_html):
    parser = EbayParser(valid_html)
    included_components = await parser.get_included_components()
    assert included_components == "test battery"


@pytest.mark.asyncio
async def test_get_included_components_empty(empty_html):
    parser = EbayParser(empty_html)
    included_components = await parser.get_included_components()
    assert included_components is None
