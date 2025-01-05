import pytest
from checker_plus.utils import date_to_days
from unittest.mock import patch
from datetime import date


@pytest.mark.asyncio
@pytest.mark.parametrize("date, mock_today, except_result", [
    ("Fri, Nov 1", date(2024, 10, 28), "4days"),
    ("Sun, Nov 10", date(2024, 10, 28), "13days"),
    ("Fri, Jan 3", date(2024, 12, 30), "4days"),
    ("Tue, Jan 02", date(2024, 12, 24), "9days")
])
async def test_date_to_days(date, mock_today, except_result):
    with patch("checker_plus.utils.date") as mock_date:
        mock_date.today.return_value = mock_today
        result = await date_to_days(date)
        assert result == except_result
