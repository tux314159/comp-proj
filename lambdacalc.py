#!/usr/bin/python
from enum import Enum
from functools import wraps
from typing import Any


class TokT(Enum):
    BRACO = 1
    BRACC = 2
    LAMBD = 3
    VNAME = 4
    SEPAR = 5
    APPLY = 6
    ENDST = 7
    ERROR = 8


TokStream = list[tuple[TokT, str]]


def lex(stream: str) -> TokStream:
    """
    Tokenise input stream into a stream of tokens.
    This is really simple, ugly code but it works.
    """
    toks = []
    reading_name: list[str] = []
    for c in stream:
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
        elif c == "/":
            toks.append((TokT.APPLY, c))
        elif c.isalpha():
            reading_name.append(c)
            continue
        else:
            toks.append((TokT.ERROR, ""))

    if len(reading_name) > 0:
        toks.append((TokT.VNAME, "".join(reading_name)))

    return toks


class AstT(Enum):
    ABSTR = 1
    APPLY = 2
    NAME = 3


class Parser:
    """
    Recursive-descent parser for lambda calc expressions.
    This is put into a class because it has a bunch of internal state.
    Because I suck at this and recursive descent is kind of finnicky, this
    parser is basically "maximal munch" (everything associates left).
    """

    def __init__(self, stream: TokStream) -> None:
        self.stream = iter(stream)
        self.bindings: set[str] = set()
        self.ctok: tuple[TokT, str] = next(self.stream)

    def die(self, msg: str):
        raise SyntaxError(f"{msg} @ '{self.ctok[1]}' ({self.ctok[0]})")

    def next_tok(self):
        self.ctok = next(self.stream)

    @staticmethod
    def subexpr_parser(parser):
        """
        Decorator to indicate it's part of the actual recursive-descent parsing
        routines.
        """
        @wraps(parser)
        def inner(self, *args, **kwargs):
            print(parser.__name__, self.ctok)
            try:
                return parser(self, *args, **kwargs)
            except StopIteration:
                return None

        return inner

    @subexpr_parser
    def parse_expr(self):
        node = []

        while self.ctok[0] == TokT.VNAME or self.ctok[0] == TokT.LAMBD or self.ctok[0] == TokT.BRACO:
            curnode = []
            if self.ctok[0] == TokT.VNAME:
                curnode = self.parse_var(False)
            elif self.ctok[0] == TokT.LAMBD:
                curnode = self.parse_lambda()
            elif self.ctok[0] == TokT.BRACO:
                self.parse_brac()
                curnode = self.parse_expr()
                self.parse_brac()
            node = curnode if len(node) == 0 else [AstT.APPLY, node, curnode]

        return node

    @subexpr_parser
    def parse_lambda(self):
        if self.ctok[0] != TokT.LAMBD:
            self.die(f"expected lambda")
        self.next_tok()
        node: list[AstT | Any] = [AstT.ABSTR]
        node.append(self.parse_var(True))
        self.parse_dot()
        node.append(self.parse_expr())
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
    def parse_var(self, is_binder: bool):
        if self.ctok[0] != TokT.VNAME:
            self.die("expected name")

        if is_binder:
            if self.ctok[1] in self.bindings:
                self.die("shadow")
            self.bindings.add(self.ctok[1])
        else:
            if self.ctok[1] not in self.bindings:
                self.die("bad reference")

        node = [AstT.NAME, self.ctok[1]]
        self.next_tok()
        return node


parser = Parser(lex("(\\f.f f)(\\ff.\\x.ff ff x)"))
print(parser.parse_expr())
