from . import parsec as p
from .parsec import generate

join_chars = lambda chars: "".join(chars)


@generate
def until_eol():
    text = yield p.many(p.exclude(p.any(), eol)).parsecmap(join_chars)
    yield eol
    return text


@generate
def eol():
    new_line = yield p.string("\r\n") ^ p.string("\n")
    return new_line
