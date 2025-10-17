"""Parser for Tableau expressions."""

from __future__ import annotations

from typing import List

from .ast import (
    BinaryOperator,
    Expression,
    Field,
    FunctionCall,
    IfExpression,
    LODExpression,
    Literal,
    NumberLiteral,
    UnaryOperator,
)
from .tokenizer import Token, TokenStream, tokenize


_PRECEDENCE = {
    "OR": 1,
    "AND": 2,
    "=": 3,
    "<": 3,
    ">": 3,
    "<=": 3,
    ">=": 3,
    "<>": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
    "^": 6,
}


def parse_expression(text: str) -> Expression:
    stream = TokenStream(tokenize(text))
    return _parse_expression(stream, 0)


def _parse_expression(stream: TokenStream, min_prec: int) -> Expression:
    token = stream.pop()
    left = _parse_primary(stream, token)

    while True:
        next_token = stream.peek()
        if not next_token or next_token.kind != "operator":
            break
        op = next_token.value
        precedence = _PRECEDENCE.get(op.upper(), 0)
        if precedence < min_prec:
            break
        stream.pop()
        right = _parse_expression(stream, precedence + 1)
        left = BinaryOperator(left=left, operator=op.upper(), right=right)
    return left


def _parse_primary(stream: TokenStream, token: Token) -> Expression:
    if token.kind == "number":
        return NumberLiteral(value=float(token.value))
    if token.kind == "string":
        return Literal(value=token.value.strip("'"))
    if token.kind == "lbracket":
        name_tokens: List[str] = []
        while True:
            next_token = stream.pop()
            if next_token.kind == "rbracket":
                break
            name_tokens.append(next_token.value)
        return Field(name="".join(name_tokens))
    if token.kind == "lbrace":
        lod_token = stream.pop()
        if lod_token.kind != "keyword":
            raise ValueError("Expected LOD keyword after '{'")
        lod_type = lod_token.value.upper()
        if lod_type not in {"FIXED", "INCLUDE", "EXCLUDE"}:
            raise ValueError(f"Unsupported LOD type {lod_type}")
        dimensions: List[Field] = []
        while True:
            next_token = stream.pop()
            if next_token.kind == "colon":
                break
            if next_token.kind == "rbrace":
                break
            if next_token.kind == "lbracket":
                name_parts: List[str] = []
                while True:
                    part = stream.pop()
                    if part.kind == "rbracket":
                        break
                    name_parts.append(part.value)
                dimensions.append(Field(name="".join(name_parts)))
        expr = _parse_expression(stream, 0)
        _expect_token(stream, "rbrace")
        return LODExpression(lod_type=lod_type, dimensions=dimensions, expression=expr)
    if token.kind == "keyword":
        keyword = token.value.upper()
        if keyword == "IF":
            condition = _parse_expression(stream, 0)
            _expect_keyword(stream, "THEN")
            then_branch = _parse_expression(stream, 0)
            else_branch = None
            if _match_keyword(stream, "ELSE"):
                else_branch = _parse_expression(stream, 0)
            _expect_keyword(stream, "END")
            return IfExpression(
                condition=condition, then_branch=then_branch, else_branch=else_branch
            )
        # function call or bare identifier
        args = _parse_argument_list(stream)
        return FunctionCall(name=keyword, arguments=args)
    if token.kind == "operator" and token.value == "-":
        operand = _parse_expression(stream, _PRECEDENCE["-"])
        return UnaryOperator(operator="-", operand=operand)
    raise ValueError(f"Unsupported token: {token}")


def _parse_argument_list(stream: TokenStream) -> List[Expression]:
    args: List[Expression] = []
    if stream.match("lparen"):
        while not stream.match("rparen"):
            args.append(_parse_expression(stream, 0))
            stream.match("comma")
        return args
    if stream.peek() and stream.peek().kind in {"keyword", "lbracket"}:
        args.append(_parse_expression(stream, 0))
    return args


def _expect_keyword(stream: TokenStream, keyword: str) -> None:
    token = stream.pop()
    if token.kind != "keyword" or token.value.upper() != keyword:
        raise ValueError(f"Expected keyword {keyword}")


def _match_keyword(stream: TokenStream, keyword: str) -> bool:
    token = stream.peek()
    if token and token.kind == "keyword" and token.value.upper() == keyword:
        stream.pop()
        return True
    return False


def _expect_token(stream: TokenStream, kind: str) -> None:
    token = stream.pop()
    if token.kind != kind:
        raise ValueError(f"Expected token {kind}")
