import os.path as path
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import List, Optional

from .. import parsec as p
from ..base import ParsedOutput, ParseResult
from ..parsec import generate
from ..util import eol, join_chars, until_eol

logger = getLogger(__name__)


@dataclass
class PytestCodeTrace:
    code: List[str]
    file: str
    line: int
    message: Optional[List[str]] = None


def parse_pytest(output: str, cwd: str = None):
    parsed_outputs, parsed_summary = pytest_output.parse(output)

    def convert_to_relative(file: str):
        if not Path(file).is_absolute():
            return file
        return path.relpath(file, cwd)

    parsed_results = {
        (convert_to_relative(r.file), r.name, *r.namespaces): r
        for r in [*parsed_summary, *parsed_outputs]
        if r
    }
    return ParsedOutput(results=list(parsed_results.values()))


@generate
def pytest_output():
    yield pytest_test_results_summary
    parsed_outputs = yield p.many1(failed_test_section)
    parsed_summary = yield pytest_summary_info
    return parsed_outputs, parsed_summary


@generate
def failed_test_section():
    namespaces, test_name = yield failed_test_section_title
    raw_output_lines = yield p.many1(
        p.exclude(until_eol, failed_test_section_title ^ pytest_summary_info_title)
    )
    output_text = "\n".join(raw_output_lines) + "\n"
    try:

        file, err_msg, err_line = (
            failed_test_section_output ^ failed_test_section_collection_error
        ).parse(output_text)
        return ParseResult(
            name=test_name,
            namespaces=namespaces,
            file=file,
            message=err_msg,
            line=err_line,
        )
    except Exception as e:
        logger.debug(f"Failed to parse output: {e}\n----\n{output_text}\n----")
        return None


@generate
def failed_test_section_output():
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
    return (
        test_file,
        error_message,
        test_line_no,
    )


@generate
def failed_test_section_collection_error():
    yield p.string("Traceback") >> until_eol
    test_file = (
        yield p.many1(p.string(" "))
        >> p.string('File "')
        >> p.many1(p.none_of('"')).parsecmap(join_chars)
        << p.string('", ')
    )
    test_line_no = (
        yield p.string("line ")
        >> p.many1(p.digit()).parsecmap(join_chars).parsecmap(int)
        << until_eol
    )
    yield p.many1(p.string(" ") >> until_eol)
    error_message = yield until_eol
    return (
        test_file,
        [error_message],
        test_line_no,
    )


@generate
def failed_test_section_title():
    yield p.string("_") >> p.many1(p.string("_")) >> p.space()
    name_elements = (
        yield p.many1(p.none_of(" ["))
        .parsecmap(join_chars)
        .parsecmap(lambda elems: elems.split("."))
    )
    namespaces = name_elements[:-1]
    test_name = name_elements[-1]
    yield until_eol
    return (namespaces, test_name)


@generate
def failed_test_captured_output_sections():
    sections = yield p.many(failed_test_captured_output)
    return dict(sections)


failed_test_section_sep = p.many1(p.one_of("_ ")) >> eol


@generate
def failed_test_code_sections():
    sections = yield p.sepBy1(failed_test_code_section, failed_test_section_sep)
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
def pytest_summary_failed_test():
    yield p.string("FAILED ")
    names = yield p.sepBy1(
        p.many1(p.none_of(": ")).parsecmap(join_chars), p.string("::")
    )
    file, *namespaces = names
    yield until_eol
    return ParseResult(
        name=namespaces[-1],
        namespaces=namespaces[:-1],
        file=file,
    )


@generate
def pytest_summary_info():
    yield pytest_summary_info_title
    parsed_summary = yield p.many1(pytest_summary_failed_test)
    yield p.many(until_eol)
    return parsed_summary


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
