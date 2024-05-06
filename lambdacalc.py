#!/usr/bin/python
from enum import Enum
from functools import reduce, wraps
from typing import Any


class TokT(Enum):
    BRACO = 1
    BRACC = 2
    LAMBD = 3
    VNAME = 4
    SEPAR = 5
    ENDST = 6
    ERROR = 7


TokStream = list[tuple[TokT, str]]


def lex(stream: str) -> TokStream:
    """Tokenise input stream into a stream of tokens."""
    toks = []
    reading_name: list[str] = []
    for c in stream:
        # This is quite ugly lol but it works
        if not c.isalpha():
            if len(reading_name) > 0:
                toks.append((TokT.VNAME, "".join(reading_name)))
            reading_name.clear()

        if c.isspace():
            continue
        elif c == "(":
            toks.append((TokT.BRACO, c))
        elif c == ")":
            toks.append((TokT.BRACC, c))
        elif c == "\\":
            toks.append((TokT.LAMBD, c))
        elif c == ".":
            toks.append((TokT.SEPAR, c))
        elif c.isalpha():
            reading_name.append(c)
            continue
        else:
            toks.append((TokT.ERROR, ""))

    # ...
    if len(reading_name) > 0:
        toks.append((TokT.VNAME, "".join(reading_name)))
    toks.append((TokT.ENDST, ""))

    return toks


class AstT(Enum):
    ABSTR = 1
    APPLY = 2
    NAME = 3


class Parser:
    """Recursive-descent parser for lambda calc expressions.
    This is put into a class because it has a bunch of internal state.
    Note that everything associates left by default.
    """

    def __init__(self, stream: TokStream) -> None:
        self.stream = iter(stream)  # our token stream
        self.bindings: list[set[str]] = []  # variable binding stack
        self.ctok: tuple[TokT, str] = next(self.stream)  # current token

    def die(self, msg: str):
        raise SyntaxError(f"{msg} @ '{self.ctok[1]}' ({self.ctok[0]})")

    def next_tok(self):
        self.ctok = next(self.stream)

    @staticmethod
    def subexpr_parser(parser):
        """Decorator for _all_ parsing subroutines."""

        @wraps(parser)
        def inner(self, *args, **kwargs):
            # print(parser.__name__, self.ctok)
            return parser(self, *args, **kwargs)

        return inner

    def parse(self):
        """Parser entry point"""
        return self.parse_expr()

    @subexpr_parser
    def parse_expr(self):
        """Parse a whole expression; notice we don't munch any tokens."""
        node = []

        while self.ctok[0] != TokT.ENDST and self.ctok[0] != TokT.BRACC:
            curnode = []
            if self.ctok[0] == TokT.VNAME:
                curnode = self.parse_var(is_bind=False)
            elif self.ctok[0] == TokT.LAMBD:
                curnode = self.parse_lambda()
            elif self.ctok[0] == TokT.BRACO:
                self.parse_brac()
                curnode = self.parse_expr()
                self.parse_brac()
            else:
                self.die("unexpected token")
            node = curnode if len(node) == 0 else [AstT.APPLY, node, curnode]

        return node

    @subexpr_parser
    def parse_lambda(self):
        """Parse a lambda expression and deal with scoping."""
        if self.ctok[0] != TokT.LAMBD:
            self.die(f"expected lambda")

        # Add new scope
        self.bindings.append(set())

        # Parse
        node: list[AstT | Any] = [AstT.ABSTR]
        self.next_tok()
        node.append(self.parse_var(is_bind=True))
        self.parse_dot()
        node.append(self.parse_expr())

        # Remove variables from scope
        self.bindings.pop()

        return node

    @subexpr_parser
    def parse_dot(self):
        if self.ctok[0] != TokT.SEPAR:
            self.die("expected seperator")
        self.next_tok()

    @subexpr_parser
    def parse_brac(self):
        if self.ctok[0] != TokT.BRACO and self.ctok[0] != TokT.BRACC:
            self.die("expected bracket")
        self.next_tok()

    @subexpr_parser
    def parse_var(self, is_bind: bool):
        if self.ctok[0] != TokT.VNAME:
            self.die("expected name")

        all_bindings = reduce(set.union, self.bindings, set())
        if is_bind:
            if self.ctok[1] in all_bindings:
                self.die("shadow")
            self.bindings[-1].add(self.ctok[1])
        else:
            if self.ctok[1] not in all_bindings:
                self.die("bad reference")

        node = [AstT.NAME, self.ctok[1]]
        self.next_tok()
        return node


print(lex("(\\f.f f)(\\f.\\x.f f x)"))
print(Parser(lex("(\\f.f f)(\\f.\\x.f f x)")).parse())
print(Parser(lex("\\f.f")).parse())
