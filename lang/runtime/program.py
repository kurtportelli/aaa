import os
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

from lang.instructions.generator import InstructionGenerator
from lang.instructions.types import Instruction
from lang.parse.models import (
    Function,
    MemberFunction,
    ParsedBuiltinsFile,
    ParsedFile,
    ParsedTypePlaceholder,
    ProgramImport,
    Struct,
    TypeLiteral,
)
from lang.parse.parser import aaa_builtins_parser, aaa_source_parser
from lang.parse.transformer import AaaTransformer
from lang.runtime.debug import format_str
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import (
    AbsoluteImportError,
    CyclicImportError,
    FileReadError,
    FunctionNameCollision,
    ImportedItemNotFound,
    MainFunctionNotFound,
    MissingEnvironmentVariable,
    TypeException,
)
from lang.typing.types import Signature, SignatureItem, TypePlaceholder, VariableType

# Identifiable are things identified uniquely by a filepath and name
Identifiable = Function | ProgramImport | Struct

# TODO clean this union up once we have better baseclasses for exceptions
FileLoadException = (
    TypeException
    | FileReadError
    | CyclicImportError
    | MainFunctionNotFound
    | MissingEnvironmentVariable
)


@dataclass(kw_only=True)
class Builtins:
    functions: Dict[str, List[Signature]]

    @classmethod
    def empty(cls) -> "Builtins":
        return Builtins(functions={})


class Program:
    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self.function_instructions: Dict[Path, Dict[str, List[Instruction]]] = {}

        # Used to detect cyclic import loops
        self.file_load_stack: List[Path] = []

        self._builtins, self.file_load_errors = self._load_builtins()

        if self.file_load_errors:
            return

        self.file_load_errors = self._load_file(self.entry_point_file)

    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile(delete=False) as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def _load_builtins(self) -> Tuple[Builtins, List[FileLoadException]]:
        builtins = Builtins.empty()

        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])
        except KeyError:
            return builtins, [MissingEnvironmentVariable("AAA_STDLIB_PATH")]

        builtins_file = stdlib_path / "builtins.aaa"

        try:
            parsed_file = self._parse_builtins_file(builtins_file)
        except OSError:
            return builtins, [FileReadError(builtins_file)]

        for function in parsed_file.functions:
            if function.name not in builtins.functions:
                builtins.functions[function.name] = []

            # TODO make more DRY
            arg_types: List[SignatureItem] = []
            return_types: List[SignatureItem] = []

            for argument in function.arguments:
                if isinstance(argument.type, TypeLiteral):
                    arg_types.append(VariableType.from_type_literal(argument.type))
                elif isinstance(argument.type, ParsedTypePlaceholder):
                    arg_types.append(TypePlaceholder(argument.type.name))
                else:  # pragma: nocover
                    assert False

            for return_type in function.return_types:
                if isinstance(return_type.type, TypeLiteral):
                    return_types.append(
                        VariableType.from_type_literal(return_type.type)
                    )
                elif isinstance(return_type.type, ParsedTypePlaceholder):
                    return_types.append(TypePlaceholder(return_type.type.name))
                else:  # pragma: nocover
                    assert False

            builtins.functions[function.name].append(Signature(arg_types, return_types))

        return builtins, []

    def exit_on_error(self) -> None:  # pragma: nocover
        if not self.file_load_errors:
            return

        for error in self.file_load_errors:
            print(str(error), file=sys.stderr)
            if not str(error).endswith("\n"):
                print(file=sys.stderr)

        error_count = len(self.file_load_errors)
        maybe_s = "" if error_count == 1 else "s"
        print(f"Found {error_count} error{maybe_s}.", file=sys.stderr)
        exit(1)

    def _load_file(self, file: Path) -> List[FileLoadException]:
        # TODO make sure the file wasn't loaded already

        if file in self.file_load_stack:
            return [
                CyclicImportError(dependencies=self.file_load_stack, failed_import=file)
            ]

        self.file_load_stack.append(file)

        try:
            parsed_file = self._parse_regular_file(file)
        except OSError:
            self.file_load_stack.pop()
            return [FileReadError(file)]

        self.identifiers[file] = {}
        import_errors = self._load_imported_files(file, parsed_file)

        if import_errors:
            self.file_load_stack.pop()
            return import_errors

        try:
            self._load_file_identifiers(file, parsed_file)
        except TypeException as e:
            self.file_load_stack.pop()
            return [e]

        load_file_exceptions = self._type_check_file(file, parsed_file)
        if load_file_exceptions:
            self.file_load_stack.pop()
            return load_file_exceptions

        self.function_instructions[file] = self._generate_file_instructions(
            file, parsed_file
        )
        self.file_load_stack.pop()
        return []

    def _parse_regular_file(self, file: Path) -> ParsedFile:
        code = file.read_text()
        tree = aaa_source_parser.parse(code)
        return AaaTransformer().transform(tree)  # type: ignore

    def _parse_builtins_file(self, file: Path) -> ParsedBuiltinsFile:
        code = file.read_text()
        tree = aaa_builtins_parser.parse(code)
        return AaaTransformer().transform(tree)  # type: ignore

    def _load_file_identifiers(self, file: Path, parsed_file: ParsedFile) -> None:
        for function in parsed_file.functions:
            if function.name in self.identifiers[file]:
                raise FunctionNameCollision(file=file, function=function)

            self.identifiers[file][function.name_key()] = function

        for struct in parsed_file.structs:
            if struct.name in self.identifiers[file]:
                raise NotImplementedError

            self.identifiers[file][struct.name] = struct

    def _generate_file_instructions(
        self, file: Path, parsed_file: ParsedFile
    ) -> Dict[str, List[Instruction]]:
        file_instructions: Dict[str, List[Instruction]] = {}
        for function in parsed_file.functions:
            file_instructions[function.name_key()] = InstructionGenerator(
                file, function, self
            ).generate_instructions()
        return file_instructions

    def _type_check_file(
        self, file: Path, parsed_file: ParsedFile
    ) -> List[FileLoadException]:
        type_exceptions: List[FileLoadException] = []

        if file == self.entry_point_file:
            main_found = False
            for function in parsed_file.functions:
                if function.name == "main":
                    main_found = True
                    break

            if not main_found:
                type_exceptions.append(MainFunctionNotFound(file))

        for function in parsed_file.functions:
            try:
                TypeChecker(file, function, self).check()
            except TypeException as e:
                type_exceptions.append(e)

        return type_exceptions

    def _load_imported_files(
        self,
        file: Path,
        parsed_file: ParsedFile,
    ) -> List[FileLoadException]:
        errors: List[FileLoadException] = []

        for import_ in parsed_file.imports:
            if import_.source.startswith("/"):
                errors.append(AbsoluteImportError(file=file, node=import_))
                continue

            import_path = (file.parent / f"{import_.source}.aaa").resolve()

            import_errors = self._load_file(import_path)
            if import_errors:
                errors += import_errors
                continue

            loaded_identifiers = self.identifiers[import_path]

            for imported_item in import_.imported_items:
                if imported_item.origninal_name not in loaded_identifiers:
                    # TODO change grammar so we can more precisely point to the item that was not found
                    errors.append(
                        ImportedItemNotFound(
                            file=file,
                            node=import_,
                            imported_item=imported_item.origninal_name,
                        )
                    )
                    continue

                self.identifiers[file][imported_item.imported_name] = ProgramImport(
                    original_name=imported_item.origninal_name, source_file=import_path
                )

        return errors

    def get_identifier(self, file: Path, name: str) -> Optional[Identifiable]:
        try:
            identified = self.identifiers[file][name]
        except KeyError:
            # TODO just raise KeyError here?
            return None

        if isinstance(identified, Function):
            return identified
        elif isinstance(identified, ProgramImport):
            return self.get_identifier(identified.source_file, identified.original_name)
        elif isinstance(identified, Struct):
            return identified
        else:  # pragma: nocover
            assert False

    def get_function_source_and_name(
        self, called_from: Path, called_name: str
    ) -> Tuple[Path, str]:
        identified = self.identifiers[called_from][called_name]

        if isinstance(identified, (Function, Struct)):
            return called_from, called_name
        elif isinstance(identified, ProgramImport):
            return identified.source_file, identified.original_name
        else:  # pragma nocover
            assert False

    def get_instructions(self, file: Path, name: str) -> List[Instruction]:
        return self.function_instructions[file][name]

    def print_all_instructions(self) -> None:  # pragma: nocover
        for functions in self.function_instructions.values():
            for name, instructions in functions.items():

                if isinstance(name, MemberFunction):
                    name = f"{name.type_name}:{name.func_name}"

                func_name = format_str(name, max_length=15)

                for ip, instr in enumerate(instructions):
                    instruction = format_str(instr.__repr__(), max_length=30)

                    print(
                        f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30}",
                        file=sys.stderr,
                    )

                print(file=sys.stderr)

        print("---", file=sys.stderr)
