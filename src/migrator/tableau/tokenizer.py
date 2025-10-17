"""Simple tokenizer for Tableau formulas."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, List

_TOKEN_REGEX = re.compile(
    r"\s+"  # whitespace
    r"|(?P<number>\d+(?:\.\d+)?)"
    r"|(?P<string>'[^']*')"
    r"|(?P<lbrace>\{)"
    r"|(?P<rbrace>\})"
    r"|(?P<lbracket>\[)"
    r"|(?P<rbracket>\])"
    r"|(?P<lparen>\()"
    r"|(?P<rparen>\))"
    r"|(?P<colon>:)"
    r"|(?P<comma>,)"
    r"|(?P<operator><=|>=|<>|=|<|>|\+|-|\*|/|\^)"
    r"|(?P<word>[A-Za-z_][A-Za-z0-9_]*)"
)


@dataclass
class Token:
    kind: str
    value: str


class TokenStream:
    def __init__(self, tokens: Iterable[Token]):
        self._tokens: List[Token] = list(tokens)
        self._index = 0

    def peek(self) -> Token | None:
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def pop(self) -> Token:
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of input")
        self._index += 1
        return token

    def match(self, *kinds: str) -> Token | None:
        token = self.peek()
        if token and token.kind in kinds:
            return self.pop()
        return None


def tokenize(text: str) -> Iterator[Token]:
    """Tokenise the provided formula."""

    index = 0
    while index < len(text):
        match = _TOKEN_REGEX.match(text, index)
        if not match:
            raise ValueError(f"Unexpected character at {index}: {text[index]!r}")
        if match.lastgroup and not match.group(0).isspace():
            kind = match.lastgroup
            value = match.group(0)
            if kind == "word":
                kind = "keyword"
            yield Token(kind=kind, value=value)
        index = match.end()
