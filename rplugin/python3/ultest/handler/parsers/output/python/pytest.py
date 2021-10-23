from .. import parsec as p
from ..base import ParsedOutput, ParseResult
from ..parsec import generate

join_chars = lambda chars: "".join(chars)


@generate
def pytest_output():
    yield pytest_test_results_summary
    failed = yield p.many(failed_test_section)
    yield pytest_summary_info
    return ParsedOutput(results=failed)


@generate
def failed_test_section():
    namespaces, test_name = yield failed_test_section_title
    yield until_eol
    yield failed_test_section_code
    trace_origin = yield p.optional(until_eol >> failed_test_stacktrace)
    error_message = yield failed_test_section_error_message
    yield until_eol
    error_file, error_line_no = yield failed_test_error_location
    yield p.optional(failed_test_captured_stdout, [])
    if trace_origin:
        test_file = trace_origin[0]
        test_line_no = trace_origin[1]
    else:
        test_file = error_file
        test_line_no = error_line_no
    return ParseResult(
        name=test_name,
        namespaces=namespaces,
        file=test_file,
        message=error_message,
        line=test_line_no,
    )


@generate
def failed_test_stacktrace():
    file_name, line_no = yield failed_test_error_location
    yield p.string("_ _") >> until_eol
    yield p.many1(p.exclude(failed_test_code_line, failed_test_section_error_message))
    return file_name, line_no


@generate
def failed_test_section_title():
    yield p.many1(p.string("_")) >> p.space()
    name_elements = (
        yield p.many1(p.none_of(" "))
        .parsecmap(join_chars)
        .parsecmap(lambda elems: elems.split("."))
    )
    namespaces = name_elements[:-1]
    test_name = name_elements[-1]
    yield p.space() >> p.many1(p.string("_"))
    return (namespaces, test_name)


@generate
def failed_test_error_message_line():
    yield p.string("E")
    yield p.many(p.string(" "))
    error_text = yield until_eol
    return error_text


@generate
def failed_test_section_code():
    code = yield p.many1(
        p.exclude(
            failed_test_code_line,
            failed_test_section_error_message ^ failed_test_stacktrace,
        )
    )
    return code


@generate
def failed_test_code_line():
    error_text = yield until_eol
    return error_text


@generate
def failed_test_section_error_message():
    lines = yield p.many1(failed_test_error_message_line)
    return lines


@generate
def pytest_summary_info():
    yield p.many1(p.string("="))
    yield p.string(" short test summary info ")
    yield until_eol
    summary = yield p.many(until_eol)
    return summary


@generate
def pytest_test_results_summary():
    summary = yield p.many(p.exclude(until_eol, pytest_failed_tests_title))
    yield pytest_failed_tests_title
    return summary


@generate
def eol():
    new_line = yield p.string("\r\n") ^ p.string("\n")
    return new_line


@generate
def until_eol():
    text = yield p.many(p.exclude(p.any(), eol)).parsecmap(join_chars)
    yield eol
    return text


@generate
def failed_test_error_location():
    file_name = yield p.many1(p.none_of(" :")).parsecmap(join_chars)
    yield p.string(":")
    line_no = yield p.many1(p.digit()).parsecmap(join_chars).parsecmap(int)
    yield p.string(":")
    yield until_eol
    return file_name, line_no


@generate
def failed_test_captured_stdout():
    yield p.many1(p.string("-"))
    yield p.string(" Captured stdout call ")
    yield until_eol
    stdout = yield p.many(
        p.exclude(until_eol, failed_test_section_title ^ pytest_summary_info)
    )
    return stdout


@generate
def pytest_failed_tests_title():
    yield p.many1(p.string("="))
    yield p.string(" FAILURES ")
    yield until_eol
