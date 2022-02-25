from pathlib import Path

from lang.parser.aaa import REWRITE_RULES
from lang.parser.grammar_generator import check_grammar_file_staleness


def test_grammar_up_to_date() -> None:
    grammar_file = Path("grammar.txt")
    stale, _ = check_grammar_file_staleness(grammar_file, REWRITE_RULES)

    assert (
        not stale
    ), 'Grammar is out of date, please run "./aaa.py generate-grammar-file".'
