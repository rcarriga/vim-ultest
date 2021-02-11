import re
from typing import Dict, List, Optional

from ..models import Test
from ..vim import VimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}


class TestFinder:
    def __init__(self, vim: VimClient):
        self._vim = vim

    async def find_all(self, file_name: str, vim_patterns: Dict):
        patterns = self._convert_patterns(vim_patterns)
        with open(file_name, "r") as test_file:
            lines = test_file.readlines()
        return self._calculate_tests(file_name, patterns, lines)

    def get_nearest_from(
        self, line: int, tests: List[Test], strict: bool = False
    ) -> Optional[Test]:
        if not tests:
            return None
        l = 0
        r = len(tests) - 1
        while l <= r:
            m = int((l + r) / 2)
            mid = tests[m]
            if mid.line < line:
                l = m + 1
            elif mid.line > line:
                r = m - 1
            else:
                return mid
        return (
            tests[r] if not strict and len(tests) > r and tests[r].line < line else None
        )

    def _convert_patterns(self, vim_patterns: Dict[str, List[str]]):
        return [
            self._convert_regex(pattern) for pattern in vim_patterns.get("test", "")
        ]

    def _convert_regex(self, vim_regex: str) -> str:
        regex = vim_regex
        for pattern, repl in REGEX_CONVERSIONS.items():
            regex = re.sub(pattern, repl, regex)
        return regex

    def _calculate_tests(
        self,
        file_name: str,
        patterns: List[str],
        lines: List[str],
    ) -> List[Test]:
        tests = []
        current_test_text = ""
        for line_index, line in reversed(list(enumerate(lines))):
            test_name = self._find_test_name(line, patterns)
            if test_name:
                line_no = line_index + 1
                tests.append(
                    Test(
                        id=test_name + str(hash(current_test_text)),
                        file=file_name,
                        line=line_no,
                        col=1,
                        name=test_name,
                        running=0,
                    )
                )
                current_test_text = ""
            else:
                current_test_text += line.strip()
        return list(reversed(tests))

    def _find_test_name(self, line: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            matched = re.match(pattern, line)
            if matched:
                return matched[1]
        return None
