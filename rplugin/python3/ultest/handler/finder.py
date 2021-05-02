import re
from typing import Dict, List, Optional, Pattern, Tuple, Union

from ..models import Namespace, Test
from ..vim_client import VimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}


class PositionFinder:
    def __init__(self, vim: VimClient):
        self._vim = vim

    async def find_all(self, file_name: str, vim_patterns: Dict):
        patterns = self._convert_patterns(vim_patterns)
        self._vim.log.fdebug("Converted pattern {vim_patterns} to {patterns}")
        with open(file_name, "r") as test_file:
            lines = test_file.readlines()
        return self._parse_file_positions(
            file_name, patterns["test"], patterns["namespace"], lines
        )

    def get_nearest_from(
        self,
        line: int,
        positions: List[Union[Test, Namespace]],
        strict: bool = False,
        include_namespace: bool = False,
    ) -> Optional[Union[Test, Namespace]]:
        if not include_namespace:
            positions = [
                position for position in positions if isinstance(position, Test)
            ]
        if not positions:
            return None
        l = 0
        r = len(positions) - 1
        while l <= r:
            m = int((l + r) / 2)
            mid = positions[m]
            if mid.line < line:
                l = m + 1
            elif mid.line > line:
                r = m - 1
            else:
                return mid
        return (
            positions[r]
            if not strict and len(positions) > r and positions[r].line < line
            else None
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

    def _parse_file_positions(
        self,
        file_name: str,
        test_patterns: List[Pattern],
        namespace_patterns: List[Pattern],
        lines: List[str],
    ) -> List[Union[Test, Namespace]]:
        positions = []
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

            cls = None
            name = ""
            if test_name:
                cls = Test
                name = test_name
            elif namespace_name:
                cls = Namespace
                name = namespace_name
            else:
                continue

            id_suffix = hash(
                (file_name, " ".join([id for id, _ in current_namespaces]))
            )
            positions.append(
                cls(
                    id=self._clean_id(name + str(id_suffix)),
                    file=file_name,
                    line=line_no,
                    col=1,
                    name=name,
                    running=0,
                    namespaces=[id for id, _ in current_namespaces],
                )
            )
            if cls is Namespace:
                current_namespaces.append((positions[-1].id, current_indent))

        return positions

    def _clean_id(self, id: str) -> str:
        return re.subn(r"[.'\" \\/]", "_", id)[0]

    def _find_match(self, line: str, patterns: List[Pattern]) -> Optional[str]:
        for pattern in patterns:
            matched = pattern.match(line)
            if matched:
                return matched[1]
        return None
