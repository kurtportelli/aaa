from pathlib import Path
from typing import Dict, List, Tuple

from lark.lexer import Token

from lang.cross_referencer.exceptions import (
    CollidingIdentifier,
    CrossReferenceBaseException,
    ImportedItemNotFound,
    IndirectImportException,
    UnknownIdentifier,
)
from lang.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifiable,
    Identifier,
    IdentifierCallingFunction,
    IdentifierUsingArgument,
    Import,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    Unresolved,
    VariableType,
)
from lang.parser import models as parser


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self.exceptions: List[CrossReferenceBaseException] = []

    def run(self) -> CrossReferencerOutput:
        for file, parsed_file in self.parsed_files.items():
            self.identifiers[file] = self._load_identifiers(file, parsed_file)

        functions: List[Tuple[Path, Function]] = []

        for file, file_identifiers in self.identifiers.items():
            for identifiable in file_identifiers.values():
                if isinstance(identifiable, Import):
                    self._resolve_import(file, identifiable)
                elif isinstance(identifiable, Struct):
                    self._resolve_struct_fields(file, identifiable)
                elif isinstance(identifiable, Function):
                    functions.append((file, identifiable))

        for file, function in functions:
            self._resolve_function_type_params(file, function)
            self._resolve_function_arguments(file, function)
            function.body = self._resolve_function_body_identifiers(
                file, function, function.parsed.body
            )

        return CrossReferencerOutput(
            identifiers=self.identifiers, exceptions=self.exceptions
        )

    def _load_identifiers(
        self, file: Path, parsed_file: parser.ParsedFile
    ) -> Dict[str, Identifiable]:
        identifiables_list: List[Identifiable] = []
        identifiables_list += self._load_types(parsed_file.types)
        identifiables_list += self._load_structs(parsed_file.structs)
        identifiables_list += self._load_functions(parsed_file.functions)
        identifiables_list += self._load_imports(file, parsed_file.imports)

        identifiers: Dict[str, Identifiable] = {}
        for identifiable in identifiables_list:
            identifier = identifiable.identify()

            if identifier in identifiers:
                self.exceptions.append(
                    CollidingIdentifier(
                        file=file, colliding=identifiable, found=identifiers[identifier]
                    )
                )
                continue

            identifiers[identifier] = identifiable

        return identifiers

    def _load_structs(self, parsed_structs: List[parser.Struct]) -> List[Struct]:
        return [
            Struct(
                parsed=parsed_struct,
                fields={name: Unresolved() for name in parsed_struct.fields.keys()},
                name=parsed_struct.identifier.name,
            )
            for parsed_struct in parsed_structs
        ]

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        functions: List[Function] = []

        for parsed_function in parsed_functions:
            struct_name, func_name = parsed_function.get_names()

            function = Function(
                parsed=parsed_function,
                struct_name=struct_name,
                name=func_name,
                arguments={
                    arg_name: Unresolved()
                    for arg_name in parsed_function.arguments.keys()
                },
                type_params={
                    type_param.identifier.name: Unresolved()
                    for type_param in parsed_function.type_params
                },
                body=Unresolved(),
            )

            functions.append(function)

        return functions

    def _load_imports(
        self, file: Path, parsed_imports: List[parser.Import]
    ) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:

                source_file = file.parent / f"{parsed_import.source}.aaa"

                import_ = Import(
                    parsed=imported_item,
                    source_file=source_file,
                    source_name=imported_item.origninal_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                )

                imports.append(import_)

        return imports

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[Type]:
        return [
            Type(
                name=type.identifier.name,
                param_count=len(type.params.value),
                parsed=type,
            )
            for type in types
        ]

    def _resolve_import(self, file: Path, import_: Import) -> None:
        # Should not raise, the file should be parsed already at this point
        source_file_identifiers = self.identifiers[import_.source_file]

        try:
            source = source_file_identifiers[import_.source_name]
        except KeyError:
            self.exceptions.append(ImportedItemNotFound(file=file, import_=import_))
            return

        if isinstance(source, Import):
            self.exceptions.append(IndirectImportException(file=file, import_=import_))
            return

        if not isinstance(source, (Function, Struct)):
            # TODO other things cannot be imported
            # In particular: imports can't be imported as indirect importing is forbidden
            raise NotImplementedError

        import_.source = source

    def _get_identifier(self, file: Path, name: str, token: Token) -> Identifiable:
        builtin_identifiers = self.identifiers[self.builtins_path]
        file_identifiers = self.identifiers[file]

        if name in builtin_identifiers:
            found = builtin_identifiers[name]
        elif name in file_identifiers:
            found = file_identifiers[name]
        else:
            raise UnknownIdentifier(file=file, name=name, token=token)

        if isinstance(found, Import):
            assert not isinstance(found.source, (Unresolved, Import))
            return found.source

        return found

    def _resolve_struct_fields(self, file: Path, struct: Struct) -> None:
        for field_name in struct.fields:
            type_identifier = struct.parsed.fields[field_name].identifier
            type_name = type_identifier.name
            type_token = type_identifier.token

            try:
                struct.fields[field_name]
                identifier = self._get_identifier(file, type_name, type_token)
            except UnknownIdentifier as e:
                self.exceptions.append(e)
                continue

            if not isinstance(identifier, (Struct, Type)):
                # TODO unexpected identifier kind (import, function, ...)
                raise NotImplementedError

            struct.fields[field_name] = identifier

    def _resolve_function_type_params(self, file: Path, function: Function) -> None:
        for param_name in function.type_params:
            type_literal = next(
                param
                for param in function.parsed.type_params
                if param.identifier.name == param_name
            )
            type = Type(parsed=type_literal, name=param_name, param_count=0)

            # TODO raise exception if self.identifiers[file][param_name] exists

            function.type_params[param_name] = type

    def _resolve_function_arguments(self, file: Path, function: Function) -> None:
        for arg_name, parsed_arg in function.parsed.arguments.items():
            parsed_type = parsed_arg.type
            arg_type_name = parsed_arg.type.identifier.name
            type: Type

            if arg_type_name in function.type_params:
                found_type = function.type_params[arg_type_name]

                assert isinstance(found_type, Type)
                type = found_type

                params: List[VariableType] = []
                is_placeholder = True
            else:
                is_placeholder = False

                try:
                    identifier = self._get_identifier(
                        file, parsed_type.identifier.name, parsed_type.identifier.token
                    )
                except UnknownIdentifier as e:
                    self.exceptions.append(e)
                    continue

                if not isinstance(identifier, Type):
                    # TODO handle
                    raise NotImplementedError

                type = identifier

                if len(parsed_type.params.value) != 0:
                    # TODO handle type params
                    raise NotImplementedError

                params = []

            function.arguments[arg_name] = VariableType(
                parsed=parsed_type,
                type=type,
                name=arg_name,
                params=params,
                is_placeholder=is_placeholder,
            )

    def _resolve_function_body_identifiers(
        self, file: Path, function: Function, parsed: parser.FunctionBody
    ) -> FunctionBody:
        items: List[FunctionBodyItem] = []

        for parsed_item in parsed.items:
            item: FunctionBodyItem

            if isinstance(parsed_item, parser.Identifier):
                if parsed_item.name in function.arguments:
                    arg_type = function.arguments[parsed_item.name]
                    item = Identifier(
                        **parsed.dict(), kind=IdentifierUsingArgument(arg_type=arg_type)
                    )
                else:
                    try:
                        identifiable = self._get_identifier(
                            file, parsed_item.name, parsed_item.token
                        )
                    except UnknownIdentifier:
                        # TODO calling non-existing function
                        raise NotImplementedError

                    if isinstance(identifiable, Function):
                        item = Identifier(
                            **parsed.dict(),
                            kind=IdentifierCallingFunction(function=identifiable),
                        )
                    elif isinstance(identifiable, Struct):
                        # TODO put struct literal on stack
                        raise NotImplementedError
                    else:  # pragma: nocover
                        raise NotImplementedError

            elif isinstance(parsed_item, parser.IntegerLiteral):
                item = IntegerLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StringLiteral):
                item = StringLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.BooleanLiteral):
                item = BooleanLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.Operator):
                item = Operator(**parsed_item.dict())
            elif isinstance(parsed_item, parser.Loop):
                item = Loop(
                    condition=self._resolve_function_body_identifiers(
                        file, function, parsed_item.condition
                    ),
                    body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.body
                    ),
                )
            elif isinstance(parsed_item, parser.Branch):
                item = Branch(
                    condition=self._resolve_function_body_identifiers(
                        file, function, parsed_item.condition
                    ),
                    if_body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.if_body
                    ),
                    else_body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.else_body
                    ),
                )
            elif isinstance(parsed_item, parser.MemberFunctionLiteral):
                item = MemberFunctionName(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StructFieldQuery):
                item = StructFieldQuery(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StructFieldUpdate):
                item = StructFieldUpdate(**parsed_item.dict())
            elif isinstance(parsed_item, parser.FunctionBody):
                item = self._resolve_function_body_identifiers(
                    file, function, parsed_item
                )
            else:  # pragma: nocover
                assert False

            items.append(item)

        return FunctionBody(items=items)
