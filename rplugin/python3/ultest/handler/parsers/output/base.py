import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set

from .parsec import ParseError


@dataclass(frozen=True)
class ParseResult:
    name: str
    namespaces: List[str]
    file: str
    message: Optional[List[str]] = None
    output: Optional[List[str]] = None
    line: Optional[int] = None


@dataclass(frozen=True)
class ParsedOutput:
    results: List[ParseResult]


_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class BaseParser(ABC):
    @property
    @abstractmethod
    def runners(self) -> Set[str]:
        ...

    @abstractmethod
    def parse(self, output: str) -> ParsedOutput:
        ...

    def parse_ansi(self, output: str) -> ParsedOutput:
        clean_output, _ = _ANSI_ESCAPE.subn("", output)
        try:
            return self.parse(clean_output.replace("\r\n", "\n"))
        except ParseError:
            return ParsedOutput(results=[])
