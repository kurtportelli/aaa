from __future__ import annotations

from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser.models import Tree
from parser.tokenizer.models import Token
from typing import Dict, List, Optional, Type, Union

from lang.grammar.parser import NonTerminal, Terminal

FunctionBodyItem = Union[
    "BooleanLiteral",
    "Branch",
    "Identifier",
    "IntegerLiteral",
    "Loop",
    "MemberFunction",
    "Operator",
    "StringLiteral",
    "StructFieldQuery",
    "StructFieldUpdate",
    "TypeLiteral",
]


@dataclass(kw_only=True)
class AaaTreeNode:
    token_offset: int
    token_count: int

    @abstractclassmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "AaaTreeNode":  # pragma: nocover
        ...


@dataclass(kw_only=True)
class IntegerLiteral(AaaTreeNode):
    value: int

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "IntegerLiteral":
        assert tree.token_type == Terminal.INTEGER
        value = int(tree.value(tokens, code))
        return IntegerLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class StringLiteral(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "StringLiteral":
        assert tree.token_type == Terminal.STRING
        value = (
            tree.value(tokens, code)[1:-1]
            .replace("\\\\", "\\")
            .replace("\\n", "\n")
            .replace('\\"', '"')
        )
        return StringLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "BooleanLiteral":
        assert tree.token_type == NonTerminal.BOOLEAN
        value = tree.value(tokens, code) == "true"
        return BooleanLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class TypeLiteral(AaaTreeNode):
    type_name: str
    type_parameters: List[ParsedType]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "TypeLiteral":
        assert tree.token_type == NonTerminal.TYPE_LITERAL

        type_name = tree[0].value(tokens, code)
        type_parameters: List[ParsedType] = []

        if len(tree.children) > 1:
            for param in tree[1].children[1:-1:2]:
                type_parameters.append(ParsedType.from_tree(param, tokens, code))

        return TypeLiteral(
            type_name=type_name,
            type_parameters=type_parameters,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Operator(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Operator":
        assert tree.token_type == NonTerminal.OPERATOR
        operator = tree.value(tokens, code)
        return Operator(
            value=operator, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class Loop(AaaTreeNode):
    condition: "FunctionBody"
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Loop":
        assert tree.token_type == NonTerminal.LOOP

        condition = FunctionBody.from_tree(tree.children[1], tokens, code)
        loop_body = FunctionBody.from_tree(tree.children[3], tokens, code)
        return Loop(
            condition=condition,
            body=loop_body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Identifier(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Identifier":
        name = tree.value(tokens, code)
        return Identifier(
            name=name, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class Branch(AaaTreeNode):
    condition: "FunctionBody"
    if_body: "FunctionBody"
    else_body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Branch":
        assert tree.token_type == NonTerminal.BRANCH

        condition = FunctionBody.from_tree(tree[1], tokens, code)
        if_body = FunctionBody.from_tree(tree[3], tokens, code)

        if len(tree.children) == 7:
            else_body = FunctionBody.from_tree(tree[5], tokens, code)
        else:
            else_body = FunctionBody(
                items=[], token_count=tree.token_count, token_offset=tree.token_offset
            )

        return Branch(
            condition=condition,
            if_body=if_body,
            else_body=else_body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class MemberFunction(AaaTreeNode):
    type_name: str
    func_name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "MemberFunction":
        assert tree.token_type == NonTerminal.MEMBER_FUNCTION

        type_name = tree[0].value(tokens, code)
        func_name = tree[2].value(tokens, code)

        return MemberFunction(
            type_name=type_name,
            func_name=func_name,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class StructFieldQuery(AaaTreeNode):
    field_name: str

    @classmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "StructFieldQuery":
        assert tree.token_type == NonTerminal.STRUCT_FIELD_QUERY

        field_name = StringLiteral.from_tree(tree[0], tokens, code).value

        return StructFieldQuery(
            field_name=field_name,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class StructFieldUpdate(AaaTreeNode):
    field_name: str
    new_value_expr: FunctionBody

    @classmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "StructFieldUpdate":
        assert tree.token_type == NonTerminal.STRUCT_FIELD_UPDATE

        field_name = StringLiteral.from_tree(tree[0], tokens, code).value
        new_value_expr = FunctionBody.from_tree(tree[1], tokens, code)

        return StructFieldUpdate(
            field_name=field_name,
            new_value_expr=new_value_expr,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "FunctionBody":
        assert tree.token_type == NonTerminal.FUNCTION_BODY

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            NonTerminal.BOOLEAN: BooleanLiteral,
            NonTerminal.BRANCH: Branch,
            NonTerminal.LOOP: Loop,
            NonTerminal.MEMBER_FUNCTION: MemberFunction,
            NonTerminal.OPERATOR: Operator,
            NonTerminal.STRUCT_FIELD_QUERY: StructFieldQuery,
            NonTerminal.STRUCT_FIELD_UPDATE: StructFieldUpdate,
            NonTerminal.TYPE_LITERAL: TypeLiteral,
            Terminal.IDENTIFIER: Identifier,
            Terminal.INTEGER: IntegerLiteral,
            Terminal.STRING: StringLiteral,
        }

        items: List[FunctionBodyItem] = []

        for child in tree.children:
            aaa_tree_node = aaa_tree_nodes[child.token_type]
            items.append(aaa_tree_node.from_tree(child, tokens, code))

        return FunctionBody(
            items=items, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class ParsedTypePlaceholder(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "ParsedTypePlaceholder":
        assert tree.token_type == NonTerminal.TYPE_PLACEHOLDER

        return ParsedTypePlaceholder(
            name=tree[1].value(tokens, code),
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ParsedType(AaaTreeNode):
    type: Union[TypeLiteral, ParsedTypePlaceholder]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ParsedType":
        assert tree.token_type == NonTerminal.TYPE

        type: Union[TypeLiteral, ParsedTypePlaceholder]

        if tree[0].token_type == NonTerminal.TYPE_LITERAL:
            type = TypeLiteral.from_tree(tree[0], tokens, code)

        elif tree[0].token_type == NonTerminal.TYPE_PLACEHOLDER:
            type = ParsedTypePlaceholder.from_tree(tree[0], tokens, code)

        else:  # pragma: nocover
            assert False

        return ParsedType(
            type=type,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Argument(AaaTreeNode):
    name: str
    type: ParsedType

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Argument":
        assert tree.token_type == NonTerminal.ARGUMENT

        return Argument(
            name=tree[0].value(tokens, code),
            type=ParsedType.from_tree(tree[2], tokens, code),
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Function(AaaTreeNode):
    name: str
    arguments: List[Argument]
    return_types: List[ParsedType]
    body: FunctionBody

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Function":
        assert tree.token_type == NonTerminal.FUNCTION_DEFINITION

        name = tree[1].value(tokens, code)
        arguments: List[Argument] = []
        return_types: List[ParsedType] = []

        index = 2

        while True:
            token_type = tree[index].token_type

            if token_type == Terminal.ARGS:
                arguments = [
                    Argument.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

            elif token_type == Terminal.RETURN:
                return_types = [
                    ParsedType.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

            elif token_type == Terminal.BEGIN:
                body = FunctionBody.from_tree(tree[index + 1], tokens, code)
                break

            else:  # pragma: nocover
                assert False

            index += 2

        return Function(
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ImportItem(AaaTreeNode):
    origninal_name: str
    imported_name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ImportItem":
        assert tree.token_type == NonTerminal.IMPORT_ITEM

        origninal_name = tree[0].value(tokens, code)

        if len(tree.children) == 3:
            imported_name = tree[2].value(tokens, code)
        else:
            imported_name = tree[0].value(tokens, code)

        return ImportItem(
            origninal_name=origninal_name,
            imported_name=imported_name,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Import(AaaTreeNode):
    source: str
    imported_items: List[ImportItem]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Import":
        assert tree.token_type == NonTerminal.IMPORT_STATEMENT

        source = tree[1].value(tokens, code)[1:-1]
        imported_items = [
            ImportItem.from_tree(child, tokens, code)
            for child in tree[3].children
            if child.token_type == NonTerminal.IMPORT_ITEM
        ]

        return Import(
            source=source,
            imported_items=imported_items,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Struct(AaaTreeNode):
    name: str
    fields: List[Argument]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Struct":
        assert tree.token_type == NonTerminal.STRUCT_DEFINITION

        name = tree[1].value(tokens, code)

        fields = [
            Argument.from_tree(child, tokens, code)
            for child in tree[3].children
            if child.token_type != Terminal.COMMA
        ]

        return Struct(
            name=name,
            fields=fields,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class BuiltinFunction(AaaTreeNode):
    name: str
    arguments: List[ParsedType]
    return_types: List[ParsedType]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "BuiltinFunction":
        assert tree.token_type == NonTerminal.BUILTIN_FUNCTION_DEFINITION

        arguments: List[ParsedType] = []
        return_types: List[ParsedType] = []

        index = 2

        while index < len(tree.children):
            token_type = tree[index].token_type

            if token_type == Terminal.ARGS:
                arguments = [
                    ParsedType.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

            elif token_type == Terminal.RETURN:
                return_types = [
                    ParsedType.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

            else:  # pragma: nocover
                assert False

            index += 2

        return BuiltinFunction(
            name=StringLiteral.from_tree(tree[1], tokens, code).value,
            arguments=arguments,
            return_types=return_types,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ParsedBuiltinsFile(AaaTreeNode):
    functions: List[BuiltinFunction]

    @classmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "ParsedBuiltinsFile":
        assert tree.token_type == NonTerminal.ROOT
        assert tree.token_count == len(tokens)

        tree = tree[0]
        assert tree.token_type == NonTerminal.BUILTINS_FILE_ROOT

        functions: List[BuiltinFunction] = []

        for child in tree.children:
            if child.token_type == NonTerminal.BUILTIN_FUNCTION_DEFINITION:
                function = BuiltinFunction.from_tree(child, tokens, code)
                functions.append(function)

            else:  # pragma: nocover
                assert False

        return ParsedBuiltinsFile(
            functions=functions,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ParsedFile(AaaTreeNode):
    functions: List[Function]
    imports: List[Import]
    structs: List[Struct]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ParsedFile":
        assert tree.token_type == NonTerminal.ROOT
        assert tree.token_count == len(tokens)

        tree = tree[0]
        assert tree.token_type == NonTerminal.REGULAR_FILE_ROOT

        functions: List[Function] = []
        imports: List[Import] = []
        structs: List[Struct] = []

        for child in tree.children:
            if child.token_type == NonTerminal.FUNCTION_DEFINITION:
                function = Function.from_tree(child, tokens, code)
                functions.append(function)

            elif child.token_type == NonTerminal.IMPORT_STATEMENT:
                import_ = Import.from_tree(child, tokens, code)
                imports.append(import_)

            elif child.token_type == NonTerminal.STRUCT_DEFINITION:
                struct = Struct.from_tree(child, tokens, code)
                structs.append(struct)

            else:  # pragma: nocover
                assert False

        return ParsedFile(
            functions=functions,
            imports=imports,
            structs=structs,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )
