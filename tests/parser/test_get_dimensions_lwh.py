import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_dimensions_lwh_valid(valid_html):
    parser = EbayParser(valid_html)
    dimensions_lwh = await parser.get_dimensions_lwh()
    assert dimensions_lwh == "test length x test width x test height"


@pytest.mark.asyncio
async def test_get_dimensions_lwh_empty(empty_html):
    parser = EbayParser(empty_html)
    dimensions_lwh = await parser.get_dimensions_lwh()
    assert dimensions_lwh is None
