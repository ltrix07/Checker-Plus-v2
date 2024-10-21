import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_part_number_valid(valid_html):
    parser = EbayParser(valid_html)
    part_number = await parser.get_part_number()
    assert part_number == "TEST57433577"


@pytest.mark.asyncio
async def test_get_part_number_empty(empty_html):
    parser = EbayParser(empty_html)
    part_number = await parser.get_part_number()
    assert part_number is None
