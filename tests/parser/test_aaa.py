from typing import List

import pytest

from lang.parser.aaa import (
    KEYWORDS,
    OPERATOR_KEYWORDS,
    REWRITE_RULES,
    SymbolType,
    parse,
)
from lang.parser.generic import ParseError, new_parse_generic


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("true", True),
        ("false", True),
        ("truea", False),
        ("truefalse", False),
        ("falsetrue", False),
    ],
)
def test_parse_boolean_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.BOOLEAN_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("1", True),
        ("0", True),
        ("00", True),
        ("1", True),
        ("9", True),
        ("123", True),
        ("-1", False),
        ("a1", False),
        ("1a", False),
    ],
)
def test_parse_integer_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.INTEGER_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ('"', False),
        ('""', True),
        ('"aasdfasdf"', True),
        ('"\\\\"', True),
        ('"\\n"', True),
        ('"\\""', True),
        ('"asdf \\\\ asdf \\n asdf \\""', True),
    ],
)
def test_parse_string_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.STRING_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ('"', False),
        ('""', True),
        ('"aasdfasdf"', True),
        ('"\\\\"', True),
        ('"\\n"', True),
        ('"\\""', True),
        ('"asdf \\\\ asdf \\n asdf \\""', True),
        ("1", True),
        ("123456", True),
        ("0", True),
        ("0a", False),
        ("00", True),
        ("true", True),
        ("false", True),
    ],
)
def test_parse_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("a", True),
        ("0", False),
        ("/", False),
        ("z", True),
        ("_", True),
        ("A", False),
        ("Z", False),
        ("abcd_xyz", True),
        ("abcd_xyz/", False),
    ]
    + [(identifier, False) for identifier in KEYWORDS],
)
def test_parse_identifier(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.IDENTIFIER, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("foo", False),
        ("<=>", False),
    ]
    + [(op, True) for op in OPERATOR_KEYWORDS],
)
def test_parse_operation(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.OPERATION, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", True),
        ("abc", False),
        (" ", True),
        ("\n", True),
        ("  ", True),
        ("\n\n", True),
        (" \n \n", True),
        ("\n \n ", True),
        (" \na", False),
    ],
)
def test_parse_whitespace(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.WHITESPACE, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("else end", False),
        ("end", False),
        ("foo", False),
        ("if end", True),
        ("if\nend", True),
        ("if\n end", True),
        ("if a end", True),
        ("if\na\nend", True),
        ("if \na \nend", True),
        ('if \n123 true and <= "\\\\  \\n  \\" " \nend', True),
        ("if else end", True),
        ("if\nelse\nend", True),
        ("if\n else\n end", True),
        ("if a else a end", True),
        ("if\na\nelse\na\nend", True),
        ("if \na \nelse \na \nend", True),
        (
            'if \n123 true and <= "\\\\  \\n  \\" " \nelse \n123 true and <= "\\\\  \\n  \\" " \nend',
            True,
        ),
        ("if if end end", True),
        ("if if if if end end end end", True),
        ("if if else end else if else end end", True),
        ("if while else end", False),
        ("if else while end", False),
        ("if fn else end", False),
        ("if else fn end", False),
        ("if begin else end", False),
        ("if else begin end", False),
        ("if while end end", True),
        ("if while end else end", True),
        ("if else while end end", True),
        ("if substr else end", True),
        ("if else substr end", True),
    ],
)
def test_parse_branch(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.BRANCH, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("end", False),
        ("while end", True),
        ("while a end", True),
        ("while <= end", True),
        ("while true end", True),
        ("while 123 end", True),
        ("while if end end", True),
        ("while if else end end", True),
        ("while if while end else while end end end", True),
        ("while endd end", True),
    ],
)
def test_parse_loop(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.LOOP, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("end", False),
        ("while end", True),
        ("while a end", True),
        ("if end", True),
        ("if else end", True),
        ("if a else a end", True),
        ("3 5 + < 8 true >= subst substr substr", True),
        ("if while if while if while end end end end end end", True),
    ],
)
def test_parse_function_body(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.FUNCTION_BODY, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("fn a begin end", True),
        ("fn a b begin end", True),
        ("fn a b c d e f begin end", True),
        ("fn true begin end", False),
        ("fn a true begin end", False),
        ("fn a begin 3 5 < true and end", True),
        ("fn a b c begin if while end else while end end end", True),
    ],
)
def test_parse_function(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(
            REWRITE_RULES, SymbolType.FUNCTION_DEFINITION, code, SymbolType
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("fn a begin end", True),
        (" fn a begin end", True),
        ("fn a begin end ", True),
        (" fn a begin end ", True),
        ("fn a begin end fn b begin end", True),
        (" fn a begin end fn b begin end ", True),
        ("fn a b c begin while end end fn d e f begin if else end end", True),
    ],
)
def test_parse_file(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.FILE, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_function_names", "expected_arguments"],
    [
        (" fn main begin end ", ["main"], [[]]),
        (" fn main a b c begin end ", ["main"], [["a", "b", "c"]]),
        (
            " fn main a b c begin end fn foo d e f begin end fn bar g h i begin end ",
            ["main", "foo", "bar"],
            [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]],
        ),
    ],
)
def test_file_parse_tree(
    code: str, expected_function_names: List[str], expected_arguments: List[List[str]]
) -> None:
    file = parse(code)

    assert len(file.functions) == len(expected_function_names)
    for func, expected_name, expected_args in zip(
        file.functions, expected_function_names, expected_arguments
    ):
        assert func.name == expected_name
        assert func.arguments == expected_args


# TODO test parsetree of function
# TODO test parsetree of branch
# TODO test parsetree of identifier
# TODO test parsetree of 3 literal types
# TODO test parsetree of loop
# TODO test parsetree of operations
# TODO test parsetree of compilcated example
