from typing import List, Type

import pytest

from tests.aaa_code import check_aaa_code


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("1 2 + .", "3", [], id="add-basic"),
        pytest.param("2 3 * .", "6", [], id="multiply-basic"),
        pytest.param("3 2 - .", "1", [], id="subtract-positive-result"),
        pytest.param("3 5 - .", "-2", [], id="subtract-negative-result"),
        pytest.param("6 3 / .", "2", [], id="devide-ok-evenly"),
        pytest.param("7 3 / .", "2", [], id="devide-ok-unevenly"),
        pytest.param("7 0 / .", "", [], id="devide-by-zero", marks=pytest.mark.skip),
        pytest.param("7 3 % .", "1", [], id="modulo-ok"),
        pytest.param("7 0 % .", "", [], id="modulo-zero", marks=pytest.mark.skip),
    ],
)
def test_int_math(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_code(code, expected_output, expected_exception_types)
