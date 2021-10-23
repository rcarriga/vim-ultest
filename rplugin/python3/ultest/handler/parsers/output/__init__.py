import re
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

from ....logging import get_logger
from .base import ParseResult
from .parsec import ParseError
from .python.pytest import pytest_output


@dataclass
class OutputPatterns:
    failed_test: str
    namespace_separator: Optional[str] = None
    ansi: bool = False
    failed_name_prefix: Optional[str] = None


_BASE_PATTERNS = {
    "python#pyunit": OutputPatterns(
        failed_test=r"^FAIL: (?P<name>.*) \(.*?(?P<namespaces>\..+)\)",
        namespace_separator=r"\.",
    ),
    "go#gotest": OutputPatterns(failed_test=r"^.*--- FAIL: (?P<name>.+?) "),
    "go#richgo": OutputPatterns(
        failed_test=r"^FAIL\s\|\s(?P<name>.+?) \(.*\)",
        ansi=True,
        failed_name_prefix="Test",
    ),
    "javascript#jest": OutputPatterns(
        failed_test=r"^\s*● (?P<namespaces>.* › )?(?P<name>.*)$",
        ansi=True,
        namespace_separator=" › ",
    ),
    "elixir#exunit": OutputPatterns(failed_test=r"\s*\d\) test (?P<name>.*) \(.*\)$"),
}

# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

logger = get_logger()


class OutputParser:
    def __init__(self, disable_patterns: List[str]) -> None:
        self._parsers = {"python#pytest": pytest_output}
        self._patterns = {
            runner: patterns
            for runner, patterns in _BASE_PATTERNS.items()
            if runner not in disable_patterns
        }

    def can_parse(self, runner: str) -> bool:
        return runner in self._patterns or runner in self._parsers

    def parse_failed(self, runner: str, output: str) -> Iterable[ParseResult]:
        if runner in self._parsers:
            try:
                return self._parsers[runner].parse(_ANSI_ESCAPE.sub("", output)).results
            except ParseError:
                return []
        return self._regex_parse_failed(runner, output.splitlines())

    def _regex_parse_failed(
        self, runner: str, output: List[str]
    ) -> Iterator[ParseResult]:
        pattern = self._patterns[runner]
        fail_pattern = re.compile(pattern.failed_test)
        for line in output:
            match = fail_pattern.match(
                _ANSI_ESCAPE.sub("", line) if pattern.ansi else line
            )
            if match:
                logger.finfo(
                    "Found failed test in output {match['name']} in namespaces {match['namespaces']} of runner {runner}"
                )
                namespaces = (
                    [
                        namespace
                        for namespace in re.split(
                            pattern.namespace_separator, match["namespaces"]
                        )
                        if namespace
                    ]
                    if pattern.namespace_separator and match["namespaces"]
                    else []
                )
                name = (
                    f"{pattern.failed_name_prefix}{match['name']}"
                    if pattern.failed_name_prefix
                    else match["name"]
                )
                yield ParseResult(name=name, namespaces=namespaces, file="")
