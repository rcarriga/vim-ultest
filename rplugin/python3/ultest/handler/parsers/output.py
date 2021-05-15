import re
from dataclasses import dataclass
from typing import Iterator, List, Optional

from ...logging import UltestLogger


@dataclass(frozen=True)
class ParseResult:
    name: str
    namespaces: List[str]


@dataclass
class OutputPatterns:
    failed_test: str
    namespace_separator: Optional[str] = None
    ansi: bool = False


_BASE_PATTERNS = {
    "python#pytest": OutputPatterns(
        failed_test=r"^(FAILED|ERROR) .+?::(?P<namespaces>.+::)?(?P<name>.*?)( |$)",
        namespace_separator="::",
    ),
    "python#pyunit": OutputPatterns(
        failed_test=r"^FAIL: (?P<name>.*) \(.*?(?P<namespaces>\..+)\)",
        namespace_separator=r"\.",
    ),
    "go#gotest": OutputPatterns(failed_test=r"^--- FAIL: (?P<name>.+?) "),
    "javascript#jest": OutputPatterns(
        failed_test=r"^\s*● (?P<namespaces>.* › )?(?P<name>.*)$",
        ansi=True,
        namespace_separator=" › ",
    ),
    "elixir#exunit": OutputPatterns(failed_test=r"\s*\d\) test (?P<name>.*) \(.*\)$"),
}

# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class OutputParser:
    def __init__(self, logger: UltestLogger) -> None:
        self._log = logger
        self._patterns = _BASE_PATTERNS

    def can_parse(self, runner: str) -> bool:
        return runner in self._patterns

    def parse_failed(self, runner: str, output: List[str]) -> Iterator[ParseResult]:
        pattern = self._patterns[runner]
        fail_pattern = re.compile(pattern.failed_test)
        for line in output:
            match = fail_pattern.match(
                _ANSI_ESCAPE.sub("", line) if pattern.ansi else line
            )
            if match:
                self._log.finfo(
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
                yield ParseResult(name=match["name"], namespaces=namespaces)
