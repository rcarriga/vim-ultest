# https://raw.githubusercontent.com/sighingnow/parsec.py/master/src/parsec/__init__.py
__author__ = "He Tao, sighingnow@gmail.com"

import re
from collections import namedtuple
from functools import wraps
from typing import Generic, TypeVar

##########################################################################
# Text.Parsec.Error
##########################################################################


class ParseError(RuntimeError):
    """Parser error."""

    def __init__(self, expected, text, index):
        super(ParseError, self).__init__()  # compatible with Python 2.
        self.expected = expected
        self.text = text
        self.index = index

    @staticmethod
    def loc_info(text, index):
        """Location of `index` in source code `text`."""
        if index > len(text):
            raise ValueError("Invalid index.")
        line, last_ln = text.count("\n", 0, index), text.rfind("\n", 0, index)
        col = index - (last_ln + 1)
        return (line, col)

    def loc(self):
        """Locate the error position in the source code text."""
        try:
            return "{}:{}".format(*ParseError.loc_info(self.text, self.index))
        except ValueError:
            return "<out of bounds index {!r}>".format(self.index)

    def __str__(self):
        return "expected {} at {}".format(self.expected, self.loc())


##########################################################################
# Definition the Value model of parsec.py.
##########################################################################


class Value(namedtuple("Value", "status index value expected")):
    """Represent the result of the Parser."""

    @staticmethod
    def success(index, actual):
        """Create success value."""
        return Value(True, index, actual, None)

    @staticmethod
    def failure(index, expected):
        """Create failure value."""
        return Value(False, index, None, expected)

    def aggregate(self, other=None):
        """collect the furthest failure from self and other."""
        if not self.status:
            return self
        if not other:
            return self
        if not other.status:
            return other
        return Value(True, other.index, self.value + other.value, None)

    @staticmethod
    def combinate(values):
        """aggregate multiple values into tuple"""
        prev_v = None
        for v in values:
            if prev_v:
                if not v:
                    return prev_v
            if not v.status:
                return v
        out_values = tuple([v.value for v in values])
        return Value(True, values[-1].index, out_values, None)

    def __str__(self):
        return "Value: state: {},  @index: {}, values: {}, expected: {}".format(
            self.status, self.index, self.value, self.expected
        )


##########################################################################
# Text.Parsec.Prim
##########################################################################

U = TypeVar("U")


class Parser(Generic[U]):
    """
    A Parser is an object that wraps a function to do the parsing work.
    Arguments of the function should be a string to be parsed and the index on
    which to begin parsing.
    The function should return either Value.success(next_index, value) if
    parsing successfully, or Value.failure(index, expected) on the failure.
    """

    def __init__(self, fn):
        """`fn` is the function to wrap."""
        self.fn = fn

    def __call__(self, text, index):
        """call wrapped function."""
        return self.fn(text, index)

    def parse(self, text):
        """Parses a given string `text`."""
        return self.parse_partial(text)[0]

    def parse_partial(self, text):
        """Parse the longest possible prefix of a given string.
        Return a tuple of the result value and the rest of the string.
        If failed, raise a ParseError."""
        if not isinstance(text, str):
            raise TypeError("Can only parsing string but got {!r}".format(text))
        res = self(text, 0)
        if res.status:
            return (res.value, text[res.index :])
        else:
            raise ParseError(res.expected, text, res.index)

    def parse_strict(self, text):
        """Parse the longest possible prefix of the entire given string.
        If the parser worked successfully and NONE text was rested, return the
        result value, else raise a ParseError.
        The difference between `parse` and `parse_strict` is that whether entire
        given text must be used."""
        # pylint: disable=comparison-with-callable
        # Here the `<` is not comparison.
        return (self < eof()).parse_partial(text)[0]

    def bind(self, fn):
        """This is the monadic binding operation. Returns a parser which, if
        parser is successful, passes the result to fn, and continues with the
        parser returned from fn.
        """

        @Parser
        def bind_parser(text, index):
            res = self(text, index)
            return res if not res.status else fn(res.value)(text, res.index)

        return bind_parser

    def compose(self, other):
        """(>>) Sequentially compose two actions, discarding any value produced
        by the first."""

        @Parser
        def compose_parser(text, index):
            res = self(text, index)
            return res if not res.status else other(text, res.index)

        return compose_parser

    def joint(self, *parsers):
        """(+) Joint two or more parsers into one. Return the aggregate of two results
        from this two parser."""
        return joint(self, *parsers)

    def choice(self, other):
        """(|) This combinator implements choice. The parser p | q first applies p.
        If it succeeds, the value of p is returned.
        If p fails **without consuming any input**, parser q is tried.
        NOTICE: without backtrack."""

        @Parser
        def choice_parser(text, index):
            res = self(text, index)
            return res if res.status or res.index != index else other(text, index)

        return choice_parser

    def try_choice(self, other):
        """(^) Choice with backtrack. This combinator is used whenever arbitrary
        look ahead is needed. The parser p || q first applies p, if it success,
        the value of p is returned. If p fails, it pretends that it hasn't consumed
        any input, and then parser q is tried.
        """

        @Parser
        def try_choice_parser(text, index):
            res = self(text, index)
            return res if res.status else other(text, index)

        return try_choice_parser

    def skip(self, other):
        """(<<) Ends with a specified parser, and at the end parser consumed the
        end flag."""

        @Parser
        def ends_with_parser(text, index):
            res = self(text, index)
            if not res.status:
                return res
            end = other(text, res.index)
            if end.status:
                return Value.success(end.index, res.value)
            else:
                return Value.failure(end.index, "ends with {}".format(end.expected))

        return ends_with_parser

    def ends_with(self, other):
        """(<) Ends with a specified parser, and at the end parser hasn't consumed
        any input."""

        @Parser
        def ends_with_parser(text, index):
            res = self(text, index)
            if not res.status:
                return res
            end = other(text, res.index)
            if end.status:
                return res
            else:
                return Value.failure(end.index, "ends with {}".format(end.expected))

        return ends_with_parser

    def parsecmap(self, fn):
        """Returns a parser that transforms the produced value of parser with `fn`."""
        return self.bind(
            lambda res: Parser(lambda _, index: Value.success(index, fn(res)))
        )

    def parsecapp(self, other):
        """Returns a parser that applies the produced value of this parser to the produced value of `other`."""
        # pylint: disable=unnecessary-lambda
        return self.bind(lambda res: other.parsecmap(lambda x: res(x)))

    def result(self, res):
        """Return a value according to the parameter `res` when parse successfully."""
        return self >> Parser(lambda _, index: Value.success(index, res))

    def mark(self):
        """Mark the line and column information of the result of this parser."""

        def pos(text, index):
            return ParseError.loc_info(text, index)

        @Parser
        def mark_parser(text, index):
            res = self(text, index)
            if res.status:
                return Value.success(
                    res.index, (pos(text, index), res.value, pos(text, res.index))
                )
            else:
                return res  # failed.

        return mark_parser

    def desc(self, description):
        """Describe a parser, when it failed, print out the description text."""
        return self | Parser(lambda _, index: Value.failure(index, description))

    def __or__(self, other):
        """Implements the `(|)` operator, means `choice`."""
        return self.choice(other)

    def __xor__(self, other):
        """Implements the `(^)` operator, means `try_choice`."""
        return self.try_choice(other)

    def __add__(self, other):
        """Implements the `(+)` operator, means `joint`."""
        return self.joint(other)

    def __rshift__(self, other):
        """Implements the `(>>)` operator, means `compose`."""
        return self.compose(other)

    def __irshift__(self, other):
        """Implements the `(>>=)` operator, means `bind`."""
        return self.bind(other)

    def __lshift__(self, other):
        """Implements the `(<<)` operator, means `skip`."""
        return self.skip(other)

    def __lt__(self, other):
        """Implements the `(<)` operator, means `ends_with`."""
        return self.ends_with(other)


def parse(p, text, index=0):
    """Parse a string and return the result or raise a ParseError."""
    return p.parse(text[index:])


def bind(p, fn):
    """Bind two parsers, implements the operator of `(>>=)`."""
    return p.bind(fn)


def compose(pa, pb):
    """Compose two parsers, implements the operator of `(>>)`."""
    return pa.compose(pb)


def joint(*parsers):
    """Joint two or more parsers, implements the operator of `(+)`."""

    @Parser
    def joint_parser(text, index):
        values = []
        prev_v = None
        for p in parsers:
            if prev_v:
                index = prev_v.index
            prev_v = v = p(text, index)
            if not v.status:
                return v
            values.append(v)
        return Value.combinate(values)

    return joint_parser


def choice(pa, pb):
    """Choice one from two parsers, implements the operator of `(|)`."""
    return pa.choice(pb)


def try_choice(pa, pb):
    """Choice one from two parsers with backtrack, implements the operator of `(^)`."""
    return pa.try_choice(pb)


def skip(pa, pb):
    """Ends with a specified parser, and at the end parser consumed the end flag.
    Implements the operator of `(<<)`."""
    return pa.skip(pb)


def ends_with(pa, pb):
    """Ends with a specified parser, and at the end parser hasn't consumed any input.
    Implements the operator of `(<)`."""
    return pa.ends_with(pb)


def parsecmap(p, fn):
    """Returns a parser that transforms the produced value of parser with `fn`."""
    return p.parsecmap(fn)


def parsecapp(p, other):
    """Returns a parser that applies the produced value of this parser to the produced value of `other`.
    There should be an operator `(<*>)`, but that is impossible in Python.
    """
    return p.parsecapp(other)


def result(p, res):
    """Return a value according to the parameter `res` when parse successfully."""
    return p.result(res)


def mark(p):
    """Mark the line and column information of the result of the parser `p`."""
    return p.mark()


def desc(p, description):
    """Describe a parser, when it failed, print out the description text."""
    return p.desc(description)


##########################################################################
# Parser Generator
#
# The most powerful way to construct a parser is to use the generate decorator.
# the `generate` creates a parser from a generator that should yield parsers.
# These parsers are applied successively and their results are sent back to the
# generator using `.send()` protocol. The generator should return the result or
# another parser, which is equivalent to applying it and returning its result.
#
# Note that `return` with arguments inside generator is not supported in Python 2.
# Instead, we can raise a `StopIteration` to return the result in Python 2.
#
# See #15 and `test_generate_raise` in tests/test_parsec.py
##########################################################################


def generate(fn):
    """Parser generator. (combinator syntax)."""
    if isinstance(fn, str):
        return lambda f: generate(f).desc(fn)

    @wraps(fn)
    @Parser
    def generated(text, index):
        iterator, value = fn(), None
        try:
            while True:
                parser = iterator.send(value)
                res = parser(text, index)
                if not res.status:  # this parser failed.
                    return res
                value, index = res.value, res.index  # iterate
        except StopIteration as stop:
            endval = stop.value
            if isinstance(endval, Parser):
                return endval(text, index)
            else:
                return Value.success(index, endval)
        except RuntimeError as error:
            stop = error.__cause__
            endval = stop.value
            if isinstance(endval, Parser):
                return endval(text, index)
            else:
                return Value.success(index, endval)

    return generated.desc(fn.__name__)


##########################################################################
# Text.Parsec.Combinator
##########################################################################


def times(p, mint, maxt=None):
    """Repeat a parser between `mint` and `maxt` times. DO AS MUCH MATCH AS IT CAN.
    Return a list of values."""
    maxt = maxt if maxt else mint

    @Parser
    def times_parser(text, index):
        cnt, values, res = 0, Value.success(index, []), None
        while cnt < maxt:
            res = p(text, index)
            if res.status:
                values = values.aggregate(Value.success(res.index, [res.value]))
                index, cnt = res.index, cnt + 1
            else:
                if cnt >= mint:
                    break
                else:
                    return res  # failed, throw exception.
            if cnt >= maxt:  # finish.
                break
            # If we don't have any remaining text to start next loop, we need break.
            #
            # We cannot put the `index < len(text)` in where because some parser can
            # success even when we have no any text. We also need to detect if the
            # parser consume no text.
            #
            # See: #28
            if index >= len(text):
                if cnt >= mint:
                    break  # we already have decent result to return
                else:
                    r = p(text, index)
                    if (
                        index != r.index
                    ):  # report error when the parser cannot success with no text
                        return Value.failure(
                            index, "already meets the end, no enough text"
                        )
        return values

    return times_parser


def count(p, n):
    """`count p n` parses n occurrences of p. If n is smaller or equal to zero,
    the parser equals to return []. Returns a list of n values returned by p."""
    return times(p, n, n)


def optional(p, default_value=None):
    """`Make a parser as optional. If success, return the result, otherwise return
    default_value silently, without raising any exception. If default_value is not
    provided None is returned instead.
    """

    @Parser
    def optional_parser(text, index):
        res = p(text, index)
        if res.status:
            return Value.success(res.index, res.value)
        else:
            # Return the maybe existing default value without doing anything.
            return Value.success(index, default_value)

    return optional_parser


def many(p):
    """Repeat a parser 0 to infinity times. DO AS MUCH MATCH AS IT CAN.
    Return a list of values."""
    return times(p, 0, float("inf"))


def many1(p):
    """Repeat a parser 1 to infinity times. DO AS MUCH MATCH AS IT CAN.
    Return a list of values."""
    return times(p, 1, float("inf"))


def separated(p, sep, mint, maxt=None, end=None):
    """Repeat a parser `p` separated by `s` between `mint` and `maxt` times.
    When `end` is None, a trailing separator is optional.
    When `end` is True, a trailing separator is required.
    When `end` is False, a trailing separator will not be parsed.
    MATCHES AS MUCH AS POSSIBLE.
    Return list of values returned by `p`."""
    maxt = maxt if maxt else mint

    @Parser
    def sep_parser(text, index):
        cnt, values, res = 0, Value.success(index, []), None
        sep_values = values
        while cnt < maxt:
            res = p(text, index)
            if res.status:
                values = sep_values.aggregate(Value.success(res.index, [res.value]))
                index, cnt = res.index, cnt + 1
            elif cnt < mint:
                return res  # error: need more elements, but no `p` found.
            else:
                if end in [True, None]:
                    # consume previously found trailing separator (if any)
                    values = sep_values
                break

            res = sep(text, index)
            if res.status:  # `sep` found, consume it (advance index)
                index, sep_values = res.index, Value.success(res.index, values.value)
            elif cnt < mint:
                return res  # error: need more elements, but no `sep` found.
            elif end is True:
                return res  # error: trailing separator required
            else:
                break

        return values

    return sep_parser


def sepBy(p, sep):
    """`sepBy(p, sep)` parses zero or more occurrences of p, separated by `sep`.
    Returns a list of values returned by `p`."""
    return separated(p, sep, 0, maxt=float("inf"), end=False)


def sepBy1(p, sep):
    """`sepBy1(p, sep)` parses one or more occurrences of `p`, separated by
    `sep`. Returns a list of values returned by `p`."""
    return separated(p, sep, 1, maxt=float("inf"), end=False)


def endBy(p, sep):
    """`endBy(p, sep)` parses zero or more occurrences of `p`, separated and
    ended by `sep`. Returns a list of values returned by `p`."""
    return separated(p, sep, 0, maxt=float("inf"), end=True)


def endBy1(p, sep):
    """`endBy1(p, sep) parses one or more occurrences of `p`, separated and
    ended by `sep`. Returns a list of values returned by `p`."""
    return separated(p, sep, 1, maxt=float("inf"), end=True)


def sepEndBy(p, sep):
    """`sepEndBy(p, sep)` parses zero or more occurrences of `p`, separated and
    optionally ended by `sep`. Returns a list of
    values returned by `p`."""
    return separated(p, sep, 0, maxt=float("inf"))


def sepEndBy1(p, sep):
    """`sepEndBy1(p, sep)` parses one or more occurrences of `p`, separated and
    optionally ended by `sep`. Returns a list of values returned by `p`."""
    return separated(p, sep, 1, maxt=float("inf"))


##########################################################################
# Text.Parsec.Char
##########################################################################


def any():
    """Parses a arbitrary character."""

    @Parser
    def any_parser(text, index=0):
        if index < len(text):
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "a random char")

    return any_parser


def one_of(s):
    """Parses a char from specified string."""

    @Parser
    def one_of_parser(text, index=0):
        if index < len(text) and text[index] in s:
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "one of {}".format(s))

    return one_of_parser


def none_of(s):
    """Parses a char NOT from specified string."""

    @Parser
    def none_of_parser(text, index=0):
        if index < len(text) and text[index] not in s:
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "none of {}".format(s))

    return none_of_parser


def space():
    """Parses a whitespace character."""

    @Parser
    def space_parser(text, index=0):
        if index < len(text) and text[index].isspace():
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "one space")

    return space_parser


def spaces():
    """Parses zero or more whitespace characters."""
    return many(space())


def letter():
    """Parse a letter in alphabet."""

    @Parser
    def letter_parser(text, index=0):
        if index < len(text) and text[index].isalpha():
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "a letter")

    return letter_parser


def digit():
    """Parse a digit."""

    @Parser
    def digit_parser(text, index=0):
        if index < len(text) and text[index].isdigit():
            return Value.success(index + 1, text[index])
        else:
            return Value.failure(index, "a digit")

    return digit_parser


def eof():
    """Parses EOF flag of a string."""

    @Parser
    def eof_parser(text, index=0):
        if index >= len(text):
            return Value.success(index, None)
        else:
            return Value.failure(index, "EOF")

    return eof_parser


def string(s):
    """Parses a string."""

    @Parser
    def string_parser(text, index=0):
        slen, tlen = len(s), len(text)
        if text[index : index + slen] == s:
            return Value.success(index + slen, s)
        else:
            matched = 0
            while (
                matched < slen
                and index + matched < tlen
                and text[index + matched] == s[matched]
            ):
                matched = matched + 1
            return Value.failure(index + matched, s)

    return string_parser


def regex(exp, flags=0):
    """Parses according to a regular expression."""
    if isinstance(exp, str):
        exp = re.compile(exp, flags)

    @Parser
    def regex_parser(text, index):
        match = exp.match(text, index)
        if match:
            return Value.success(match.end(), match.group(0))
        else:
            return Value.failure(index, exp.pattern)

    return regex_parser


##########################################################################
# Useful utility parsers
##########################################################################


def fail_with(message):
    return Parser(lambda _, index: Value.failure(index, message))


def exclude(p: Parser, exclude: Parser):
    """Fails parser p if parser `exclude` matches"""

    @Parser
    def exclude_parser(text, index):
        res = exclude(text, index)
        if res.status:
            return Value.failure(index, f"something other than {res.value}")
        else:
            return p(text, index)

    return exclude_parser


def lookahead(p: Parser):
    """Parses without consuming"""

    @Parser
    def lookahead_parser(text, index):
        res = p(text, index)
        if res.status:
            return Value.success(index, res.value)
        else:
            return Value.failure(index, res.expected)

    return lookahead_parser


def unit(p: Parser):
    """Converts a parser into a single unit. Only consumes input if the parser succeeds"""

    @Parser
    def unit_parser(text, index):
        res = p(text, index)
        if res.status:
            return Value.success(res.index, res.value)
        else:
            return Value.failure(index, res.expected)

    return unit_parser
