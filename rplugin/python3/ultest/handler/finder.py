import re
from typing import Dict, List, Optional, Pattern, Tuple

from ..models import Namespace, Test
from ..vim_client import VimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}


class TestFinder:
    def __init__(self, vim: VimClient):
        self._vim = vim

    async def find_all(self, file_name: str, vim_patterns: Dict):
        patterns = self._convert_patterns(vim_patterns)
        self._vim.log.fdebug("Converted pattern {vim_patterns} to {patterns}")
        with open(file_name, "r") as test_file:
            lines = test_file.readlines()
        return self._calculate_tests(
            file_name, patterns["test"], patterns["namespace"], lines
        )

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

    def _convert_patterns(
        self, vim_patterns: Dict[str, List[str]]
    ) -> Dict[str, List[Pattern]]:
        tests = [
            self._convert_regex(pattern) for pattern in vim_patterns.get("test", "")
        ]
        namespaces = [
            self._convert_regex(pattern)
            for pattern in vim_patterns.get("namespace", "")
        ]
        return {"test": tests, "namespace": namespaces}

    def _convert_regex(self, vim_regex: str) -> Pattern:
        regex = vim_regex
        for pattern, repl in REGEX_CONVERSIONS.items():
            regex = re.sub(pattern, repl, regex)
        return re.compile(regex)

    def _calculate_tests(
        self,
        file_name: str,
        test_patterns: List[Pattern],
        namespace_patterns: List[Pattern],
        lines: List[str],
    ) -> Tuple[List[Test], List[Namespace]]:
        tests = []
        namespaces = []
        current_namespaces: List[Tuple[str, int]] = []
        indent_match = re.compile(r"^\s*")
        for line_no, line in enumerate(lines, start=1):
            test_name = self._find_match(line, test_patterns)
            namespace_name = self._find_match(line, namespace_patterns)

            current_indent = len(indent_match.match(line)[0])
            while current_namespaces:
                name, indent = current_namespaces[-1]
                if namespace_name == name or indent < current_indent:
                    break
                current_namespaces.pop()

            if test_name:
                tests.append(
                    Test(
                        id=self._clean_id(
                            test_name
                            + str(
                                hash(
                                    (
                                        file_name,
                                        " ".join(
                                            [name for name, _ in current_namespaces]
                                        ),
                                    )
                                )
                            )
                        ),
                        file=file_name,
                        line=line_no,
                        col=1,
                        name=test_name,
                        running=0,
                        namespaces=[name for name, _ in current_namespaces],
                    )
                )
            elif namespace_name:
                namespaces.append(
                    Namespace(
                        id=self._clean_id(
                            namespace_name
                            + str(
                                hash(
                                    (
                                        file_name,
                                        " ".join(
                                            [name for name, _ in current_namespaces]
                                        ),
                                    )
                                )
                            )
                        ),
                        file=file_name,
                        line=line_no,
                        col=1,
                        name=namespace_name,
                    )
                )
                current_namespaces.append((namespace_name, current_indent))

        return tests, namespaces

    def _clean_id(self, id: str) -> str:
        return re.subn(r"[.'\" \\/]", "_", id)[0]

    def _find_match(self, line: str, patterns: List[Pattern]) -> Optional[str]:
        for pattern in patterns:
            matched = pattern.match(line)
            if matched:
                return matched[1]
        return None
