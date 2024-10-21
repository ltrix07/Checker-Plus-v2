import pytest
from checker_plus.checker import Checker


@pytest.mark.asyncio
@pytest.mark.parametrize("data_list, batch_size, expected_result", [
    ([
        [1, 4, 3, 2],
        [4, 67, 4, 334],
        [3445, 43, 23, 3]
    ], 1, {1: [[1, 4, 3, 2]], 2: [[4, 67, 4, 334]], 3: [[3445, 43, 23, 3]]}),
    ([
        [1, 4, 3, 2],
        [4, 67, 4, 334],
        [3445, 43, 23, 3]
    ], 2, {1: [[1, 4, 3, 2], [4, 67, 4, 334]], 2: [[3445, 43, 23, 3]]}),
    ([
        [1, 4, 3, 2],
        [4, 67, 4, 334],
        [3445, 43, 23, 3]
    ], 3, {1: [[1, 4, 3, 2], [4, 67, 4, 334], [3445, 43, 23, 3]]}),
    ([
        [1, 4, 3, 2],
        [4, 67, 4, 334],
        [3445, 43, 23, 3]
    ], 4, {1: [[1, 4, 3, 2], [4, 67, 4, 334], [3445, 43, 23, 3]]})
    ])
async def test_data_proc(data_list, batch_size, expected_result):
    ebay_checker = Checker([], [], {}, [], [])
    result = await ebay_checker.data_proc(data_list, batch_size)
    assert result == expected_result
