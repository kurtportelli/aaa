from typing import List

import pytest

from lang.exceptions import ParseError
from lang.operations import Operation, PrintInt, PushInt
from lang.parse import parse


@pytest.mark.parametrize(
    ["code", "expected_operations"],
    [
        ("", []),
        ("1", [PushInt(1)]),
        ("1 1", [PushInt(1), PushInt(1)]),
        ("123456789", [PushInt(123456789)]),
        ("print_int", [PrintInt()]),
    ],
)
def test_parse_ok(code: str, expected_operations: List[Operation]) -> None:
    assert expected_operations == parse(code)


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [("unexpectedthing", ParseError(f"Syntax error: can't handle 'unexpectedthing'"))],
)
def test_parse_fail(code: str, expected_exception: Exception) -> None:
    with pytest.raises(type(expected_exception)) as e:
        parse(code)

    expected_exception.args == e.value.args
