from .. import parsec as p
from ..base import ParsedOutput, ParseResult
from ..parsec import generate
from ..util import eol, join_chars, until_eol


class ErroredTestError(Exception):
    ...


@generate
def unittest_output():
    try:
        yield p.many(p.exclude(p.any(), failed_test_title))
        failed_tests = yield p.many1(failed_test)
        yield p.many(p.any())
        return ParsedOutput(results=failed_tests)
    except ErroredTestError:
        return ParsedOutput(results=[])


@generate
def failed_test():
    name, namespace = yield failed_test_title
    file, error_line = yield failed_test_traceback
    error_message = yield failed_test_error_message
    return ParseResult(
        name=name,
        namespaces=[namespace],
        file=file,
        message=error_message,
        line=error_line,
    )


@generate
def failed_test_title():
    text = (
        yield p.many1(p.string("="))
        >> eol
        >> (p.string("FAIL") ^ p.string("ERROR"))
        << p.string(": ")
    )
    test = yield p.many1(p.none_of(" ")).parsecmap(join_chars)
    yield p.space()
    namespace = (
        yield (p.string("(") >> p.many1(p.none_of(")")) << (p.string(")") >> until_eol))
        .parsecmap(join_chars)
        .parsecmap(lambda s: s.split(".")[-1])
    )
    if namespace == "_FailedTest":
        # Can't infer namespace from file that couldn't be imported
        raise ErroredTestError
    yield p.many1(p.string("-")) >> eol
    return test, namespace


@generate
def traceback_location():
    file = (
        yield p.spaces()
        >> p.string('File "')
        >> p.many1(p.none_of('"')).parsecmap(join_chars)
        << p.string('"')
    )
    line = yield (
        p.string(", line ")
        >> p.many1(p.digit()).parsecmap(join_chars).parsecmap(int)
        << until_eol
    )
    return file, line


@generate
def failed_test_traceback():
    yield p.string("Traceback") >> until_eol
    file, line = yield traceback_location
    yield p.many1(p.string(" ") >> until_eol)
    return file, line


@generate
def failed_test_error_message():
    message = yield p.many1(p.exclude(until_eol, p.string("--") ^ p.string("==")))
    remove_index = len(message) - 0
    for line in reversed(message):
        if line != "":
            break
        remove_index -= 1
    return message[:remove_index]  # Ends with blank lines
