from dataclasses import dataclass
from typing import List, Optional

from .. import parsec as p
from ..base import ParsedOutput, ParseResult
from ..parsec import generate
from ..util import eol, join_chars, until_eol


@dataclass
class PytestCodeTrace:
    code: List[str]
    file: str
    line: int
    message: Optional[List[str]] = None


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
    traces: List[PytestCodeTrace]
    traces = yield failed_test_code_sections
    sections = yield failed_test_captured_output_sections
    trace = traces[0]
    # Hypothesis traces provide the test definition as the first layer of trace
    if "Hypothesis" in sections and len(traces) > 1:
        trace = traces[1]
    test_file = trace.file
    test_line_no = trace.line
    error_message = None
    for trace in traces:
        if trace.message:
            error_message = trace.message
    return ParseResult(
        name=test_name,
        namespaces=namespaces,
        file=test_file,
        message=error_message,
        line=test_line_no,
    )


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
def failed_test_captured_output_sections():
    sections = yield p.many(failed_test_captured_output)
    return dict(sections)


failed_test_section_sep = p.many1(p.one_of("_ ")) >> eol


@generate
def failed_test_code_sections():

    sections = yield p.sepBy(failed_test_code_section, failed_test_section_sep)
    return sections


@generate
def failed_test_code_section():
    code = yield p.many(
        p.exclude(
            failed_test_code_line,
            failed_test_section_error_message ^ failed_test_error_location,
        )
    )
    message = yield p.optional(failed_test_section_error_message)
    if code or message:
        yield until_eol
    trace = yield failed_test_error_location
    yield p.many(
        p.exclude(
            until_eol,
            failed_test_section_sep
            ^ failed_test_captured_output_title
            ^ failed_test_section_title
            ^ pytest_summary_info_title,
        )
    )
    return PytestCodeTrace(
        code=code, file=trace and trace[0], line=trace and trace[1], message=message
    )


@generate
def failed_test_code_line():
    error_text = yield until_eol
    return error_text


@generate
def failed_test_section_error_message():
    lines = yield p.many1(failed_test_error_message_line)
    return lines


@generate
def failed_test_error_message_line():
    yield p.string("E")
    yield p.many(p.string(" "))
    error_text = yield until_eol
    return error_text


@generate
def pytest_summary_info():
    yield pytest_summary_info_title
    summary = yield p.many(until_eol)
    return summary


@generate
def pytest_summary_info_title():
    yield p.many1(p.string("="))
    yield p.string(" short test summary info ")
    yield until_eol


@generate
def pytest_test_results_summary():
    failures_title = p.many1(p.string("=")) >> p.string(" FAILURES ") >> until_eol
    summary = yield p.many(p.exclude(until_eol, failures_title))
    yield failures_title
    return summary


@generate
def failed_test_error_location():
    file_name = yield p.many1(p.none_of(" :")).parsecmap(join_chars)
    yield p.string(":")
    line_no = yield p.many1(p.digit()).parsecmap(join_chars).parsecmap(int)
    yield p.string(":")
    yield until_eol
    return file_name, line_no


@generate
def failed_test_captured_output():
    title = yield failed_test_captured_output_title.parsecmap(join_chars)
    stdout = yield p.many(
        p.exclude(
            until_eol,
            failed_test_section_title
            ^ pytest_summary_info_title
            ^ failed_test_captured_output_title,
        )
    )
    return title, stdout


@generate
def failed_test_captured_output_title():
    yield p.many1(p.string("-"))
    yield p.string(" ")
    title = yield p.many1(p.exclude(p.any(), p.string(" ---")))
    yield p.string(" ")
    yield until_eol
    return title
