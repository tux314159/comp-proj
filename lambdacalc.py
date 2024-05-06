#!/usr/bin/python
from enum import Enum
from functools import wraps
from typing import Iterator, cast


class TokT(Enum):
    BRACO = 1
    BRACC = 1
    LAMBD = 2
    VNAME = 3
    SEPAR = 4
    ERROR = 5


TokStream = list[tuple[TokT, str]]


def lex(stream: str) -> TokStream:
    """
    Tokenise input stream into a stream of tokens.
    This is really simple, ugly code but it works.
    """
    toks = []
    reading_name = []
    for c in stream:
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

        if not c.isalpha():
            if len(reading_name) > 0:
                toks.append((TokT.VNAME, "".join(reading_name)))
            reading_name.clear()

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
    """

    def __init__(self, stream: TokStream) -> None:
        self.stream = stream
        self.bindings: set[str] = set()
        self.ctok: tuple[TokT, str] = cast(tuple[TokT, str], (None, None))
        self.peek: tuple[TokT, str] = next(self.stream)

    def die(self, msg: str):
        raise SyntaxError(msg)

    @staticmethod
    def subexpr_parser(consume=True):
        """
        Helpful decorator for all subexpression parsers and advances to the
        next token (unless you tell it not to).
        """

        def subexpr_parser_(parser):
            @wraps(parser)
            def inner(self, *args, **kwargs):
                if consume:
                    self.ctok = self.peek
                    self.peek = next(self.stream)
                print(parser.__name__, self.ctok, self.peek)
                return parser(self, *args, **kwargs)

            return inner

        return subexpr_parser_

    @subexpr_parser(False)
    def parse_expr(self):
        node = []

        # Either abstraction or application!
        if self.peek[0] == TokT.LAMBD:
            node.append(AstT.ABSTR)
            node.append(self.parse_lambda())
        elif self.peek[0] == TokT.BRACO:
            self.parse_brac()
            node.append(self.parse_expr())
            self.parse_brac()

        return node

    @subexpr_parser()
    def parse_lambda(self):
        node = [AstT.ABSTR]
        node.append(self.parse_var(is_binder=True))
        self.parse_dot()
        node.append(self.parse_expr())
        return node

    @subexpr_parser()
    def parse_dot(self):
        if self.ctok[0] != TokT.SEPAR:
            self.die("expected seperator")

    @subexpr_parser()
    def parse_brac(self):
        if self.ctok[0] != TokT.BRACO and self.ctok[0] != TokT.BRACC:
            self.die("expected bracket")

    @subexpr_parser()
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

        return [AstT.NAME, self.ctok[1]]


print(list(lex(iter("\\x. x"))))
parser = Parser(lex(iter("\\x.x")))
print(parser.parse_expr())
