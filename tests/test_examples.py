from pathlib import Path
from typing import List

import pytest
from pytest import CaptureFixture

from aaa import main


@pytest.mark.skip()  # TODO re-enable
def test_readme_command(capfd: CaptureFixture[str]) -> None:
    readme_commands: List[str] = []

    with open("README.md") as readme:
        for line in readme:
            if "aaa.py cmd" in line:
                readme_commands.append(line)

    command = '"a" 0 true while over . 1 + dup 3 < end drop drop \\n'

    # README hasn't changed command and no commands were added
    assert command in readme_commands[0]
    assert len(readme_commands) == 1

    main(["./aaa.py", "cmd", command])

    stdout, _ = capfd.readouterr()
    assert str(stdout) == "aaa\n"


def expected_fizzbuzz_output() -> str:
    fizzbuzz_table = {
        0: "fizzbuzz",
        3: "fizz",
        5: "buzz",
        6: "fizz",
        9: "fizz",
        10: "buzz",
        12: "fizz",
    }

    output: List[str] = []

    for i in range(1, 101):
        output.append(fizzbuzz_table.get(i % 15, str(i)))

    return "\n".join(output) + "\n"


EXPECTED_EXAMPLE_OUTPUT = {
    "examples/one_to_ten.aaa": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n",
    "examples/print_number.aaa": "42\n",
    "examples/fizzbuzz.aaa": expected_fizzbuzz_output(),
}


@pytest.mark.skip()  # TODO re-enable
@pytest.mark.parametrize(
    ["example_file_path", "expected_output"],
    [
        (example_file_path, EXPECTED_EXAMPLE_OUTPUT[str(example_file_path)])
        for example_file_path in Path("examples").glob("**/*.aaa")
    ],
)
def test_example_commands(
    example_file_path: Path, expected_output: str, capfd: CaptureFixture[str]
) -> None:

    main(["./aaa.py", "run", str(example_file_path)])

    stdout, _ = capfd.readouterr()
    assert str(stdout) == expected_output
