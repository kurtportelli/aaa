from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from lark.exceptions import UnexpectedInput
from lark.lexer import Token
from lark.visitors import Transformer, v_args

from lang.exceptions.misc import KeywordUsedAsIdentifier
from lang.models import AaaTreeNode, FunctionBodyItem
from lang.models.parse import (
    Argument,
    BooleanLiteral,
    Branch,
    BranchCondition,
    BranchElseBody,
    BranchIfBody,
    Function,
    FunctionBody,
    Identifier,
    Import,
    ImportItem,
    IntegerLiteral,
    Loop,
    LoopBody,
    LoopCondition,
    MemberFunctionName,
    Operator,
    ParsedBuiltinsFile,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
)
from lang.models.typing.var_type import RootType, VariableType
from lang.parse.parser import aaa_keyword_parser


@v_args(inline=True)
class AaaTransformer(Transformer[Any, Any]):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    @v_args(inline=False)
    def argument_list(self, arguments: List[Argument]) -> List[Argument]:
        return arguments

    @v_args(inline=False)
    def argument(self, args: Tuple[Identifier, VariableType]) -> Argument:
        name_identifier, var_type = args
        return Argument(
            name=name_identifier.name,
            name_token=name_identifier.token,
            type=var_type,
        )

    def boolean(self, token: Token) -> BooleanLiteral:
        return BooleanLiteral(value=token.value)

    def branch(self, *args: List[AaaTreeNode]) -> Branch:
        condition: FunctionBody
        if_body: FunctionBody
        else_body = FunctionBody(items=[])

        for arg in args:
            if isinstance(arg, BranchCondition):
                condition = arg.value
            elif isinstance(arg, BranchIfBody):
                if_body = arg.value
            elif isinstance(arg, BranchElseBody):
                else_body = arg.value
            else:  # pragma: nocover
                assert False

        return Branch(condition=condition, if_body=if_body, else_body=else_body)

    def branch_condition(self, function_body: FunctionBody) -> BranchCondition:
        return BranchCondition(value=function_body)

    def branch_if_body(self, function_body: FunctionBody) -> BranchIfBody:
        return BranchIfBody(value=function_body)

    def branch_else_body(self, function_body: FunctionBody) -> BranchElseBody:
        return BranchElseBody(value=function_body)

    @v_args(inline=False)
    def builtin_function_definition(self, args: List[Any]) -> Function:
        name: str | MemberFunctionName = ""
        arguments: List[Argument] = []
        return_types: List[VariableType] = []
        token: Token

        for arg in args:
            if isinstance(arg, StringLiteral):
                name = arg.value
            elif isinstance(arg, list):
                for item in arg:
                    if isinstance(item, Argument):
                        arguments.append(item)
                    elif isinstance(item, VariableType):
                        return_types.append(item)
                    else:  # pragma: nocover
                        assert False
            elif isinstance(arg, MemberFunctionName):
                name = arg
            elif isinstance(arg, Token):
                token = arg
            else:  # pragma: nocover
                assert False

        return Function(
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=FunctionBody(items=[]),
            token=token,
        )

    @v_args(inline=False)
    def builtins_file_root(self, args: List[Function]) -> ParsedBuiltinsFile:
        functions: List[Function] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedBuiltinsFile(functions=functions)

    def function_body_item(
        self, function_body_item: FunctionBodyItem
    ) -> FunctionBodyItem:
        return function_body_item

    @v_args(inline=False)
    def function_body(self, args: List[FunctionBodyItem]) -> FunctionBody:
        return FunctionBody(items=args)

    @v_args(inline=False)
    def function_definition(self, args: List[Any]) -> Function:
        name: str | MemberFunctionName = ""
        body: FunctionBody
        arguments: List[Argument] = []
        return_types: List[VariableType] = []
        token: Token

        for arg in args:
            if isinstance(arg, Identifier):
                name = arg.name
            elif isinstance(arg, FunctionBody):
                body = arg
            elif isinstance(arg, list):
                for item in arg:
                    if isinstance(item, Argument):
                        arguments.append(item)
                    elif isinstance(item, VariableType):
                        return_types.append(item)
                    else:  # pragma: nocover
                        assert False
            elif isinstance(arg, MemberFunctionName):
                name = arg
            elif isinstance(arg, Token):
                token = arg
            else:  # pragma: nocover
                assert False

        return Function(
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=body,
            token=token,
        )

    def function_arguments(self, args: List[Argument]) -> List[Argument]:
        return args

    def function_name(
        self, name: Union[Identifier, MemberFunctionName]
    ) -> Union[Identifier, MemberFunctionName]:
        return name

    def function_return_types(self, args: List[VariableType]) -> List[VariableType]:
        return args

    def identifier(self, token: Token) -> Identifier:
        try:
            aaa_keyword_parser.parse(f"{token.value} ")
        except UnexpectedInput:
            return Identifier(name=token.value, token=token)
        else:
            # We're getting a keyword where we're expecting an identifier
            raise KeywordUsedAsIdentifier(token=token, file=self.file)

    def import_item(
        self, original_name: Identifier, imported_name: Optional[Identifier] = None
    ) -> ImportItem:
        if imported_name is None:
            imported_name = original_name

        return ImportItem(
            origninal_name=original_name.name, imported_name=imported_name.name
        )

    @v_args(inline=False)
    def import_items(self, import_items: List[ImportItem]) -> List[ImportItem]:
        assert all(isinstance(item, ImportItem) for item in import_items)
        return import_items

    def import_statement(
        self, token: Token, source: StringLiteral, imported_items: List[ImportItem]
    ) -> Import:
        return Import(source=source.value, imported_items=imported_items, token=token)

    def integer(self, token: Token) -> IntegerLiteral:
        return IntegerLiteral(value=int(token.value))

    def literal(
        self, literal: Union[IntegerLiteral, BooleanLiteral, StringLiteral]
    ) -> Union[IntegerLiteral, BooleanLiteral, StringLiteral]:
        return literal

    def loop(self, condition: LoopCondition, body: LoopBody) -> Loop:
        return Loop(condition=condition.value, body=body.value)

    def loop_condition(self, function_body: FunctionBody) -> LoopCondition:
        return LoopCondition(value=function_body)

    def loop_body(self, function_body: FunctionBody) -> LoopBody:
        return LoopBody(value=function_body)

    def member_function_name(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token)

    # TODO the token and function name needs to be improved
    def member_function(
        self, parsed_type: VariableType, func_name: Identifier
    ) -> MemberFunctionName:
        return MemberFunctionName(type_name=parsed_type.name, func_name=func_name.name)

    def operator(self, token: Token) -> Operator:
        return Operator(value=token.value)

    @v_args(inline=False)
    def regular_file_root(self, args: List[StructFieldQuery]) -> ParsedFile:
        functions: List[Function] = []
        imports: List[Import] = []
        structs: List[Struct] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            elif isinstance(arg, Struct):
                structs.append(arg)
            elif isinstance(arg, Import):
                imports.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedFile(functions=functions, imports=imports, structs=structs)

    @v_args(inline=False)
    def return_types(self, types: List[VariableType]) -> List[VariableType]:
        return types

    def string(self, token: Token) -> StringLiteral:
        assert len(token.value) >= 2

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace('\\"', '"')

        return StringLiteral(value=value)

    def struct_definition(
        self, token: Token, name: Identifier, field_list: List[Argument]
    ) -> Struct:
        fields = {field.name: field.type for field in field_list}
        return Struct(name=name.name, fields=fields, token=token)

    def struct_field_query_operator(self, token: Token) -> Token:
        return token

    def struct_field_query(
        self, field_name: StringLiteral, token: Token
    ) -> StructFieldQuery:
        return StructFieldQuery(field_name=field_name, operator_token=token)

    def struct_field_update_operator(self, token: Token) -> Token:
        return token

    def struct_field_update(
        self, field_name: StringLiteral, new_value_expr: FunctionBody, token: Token
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            field_name=field_name, new_value_expr=new_value_expr, operator_token=token
        )

    def struct_function_identifier(
        self, type_name: Identifier, func_name: Identifier
    ) -> MemberFunctionName:
        return MemberFunctionName(type_name=type_name.name, func_name=func_name.name)

    def type(self, type: VariableType) -> VariableType:
        return type

    @v_args(inline=False)
    def type_literal(self, args: List[Token | List[VariableType]]) -> VariableType:

        type_name = ""
        type_parameters: List[VariableType] = []
        for arg in args:
            if isinstance(arg, Token):
                type_name = arg.value
            elif isinstance(arg, list):
                type_parameters = arg
            elif isinstance(arg, Identifier):
                type_name = arg.name
            else:  # pragma: nocover
                assert False

        if type_name == "int":
            root_type = RootType.INTEGER
        elif type_name == "bool":
            root_type = RootType.BOOL
        elif type_name == "str":
            root_type = RootType.STRING
        elif type_name == "vec":
            root_type = RootType.VECTOR
        elif type_name == "map":
            root_type = RootType.MAPPING
        else:
            root_type = RootType.STRUCT

        return VariableType(
            name=type_name, root_type=root_type, type_params=type_parameters
        )

    @v_args(inline=False)
    def type_params(self, types: List[VariableType]) -> List[VariableType]:
        return types

    def type_placeholder(self, identifier: Identifier) -> VariableType:
        return VariableType(
            name=identifier.name, root_type=RootType.PLACEHOLDER, type_params=[]
        )
