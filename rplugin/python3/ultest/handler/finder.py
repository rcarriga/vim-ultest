import re
import json
from typing import Dict, List, Optional, Pattern, Tuple, Union

from ..models import Namespace, Test, Tree, File
from ..vim_client import VimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}

Position = Union[File, Test, Namespace]
PosList = Union[Position, List["PosList"]]


class PositionFinder:
    def __init__(self, vim: VimClient):
        self._vim = vim

    async def find_all(self, file_name: str, vim_patterns: Dict) -> Tree[Position]:
        patterns = self._convert_patterns(vim_patterns)
        self._vim.log.fdebug("Converted pattern {vim_patterns} to {patterns}")
        with open(file_name, "r") as test_file:
            lines = test_file.readlines()
        res, _ = self._parse_position_tree(
            file_name, patterns["test"], patterns["namespace"], lines
        )
        x = Tree[Position].from_list([File(id=file_name, name=file_name, file=file_name), *res])
        return x

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

    def _parse_position_tree(
        self,
        file_name: str,
        test_patterns: List[Pattern],
        namespace_patterns: List[Pattern],
        lines: List[str],
        init_line: int = 1,
        init_indent: int = -1,
        current_namespaces: Optional[List[str]] = None,
    ) -> Tuple[List[PosList], int]:
        positions = []
        indent_pattern = re.compile(r"(^\s*)\S")
        current_namespaces = current_namespaces or []
        line_no = init_line
        while line_no - init_line < len(lines):
            line = lines[line_no - init_line]
            test_name = self._find_match(line, test_patterns)
            namespace_name = self._find_match(line, namespace_patterns)

            if test_name:
                cls = Test
                name = test_name
                children = None
            elif namespace_name:
                cls = Namespace
                name = namespace_name
            else:
                line_no += 1
                continue

            current_indent = indent_pattern.match(line)
            if current_indent and len(current_indent[1]) <= init_indent:
                return positions, line_no - 1 - init_line

            id_suffix = hash((file_name, " ".join(current_namespaces)))
            position = cls(
                id=self._clean_id(name + str(id_suffix)),
                file=file_name,
                line=line_no,
                col=1,
                name=name,
                running=0,
                namespaces=current_namespaces,
            )

            if cls is Namespace:
                children, lines_consumed = self._parse_position_tree(
                    file_name,
                    test_patterns,
                    namespace_patterns,
                    lines[line_no - init_line + 1 :],
                    init_line=line_no + 1,
                    init_indent=len(current_indent[1]),
                    current_namespaces=[*current_namespaces, position.id],
                )
                positions.append([position, *children])
            else:
                lines_consumed = 1
                positions.append(position)

            line_no += lines_consumed
        return positions, line_no

    def _clean_id(self, id: str) -> str:
        return re.subn(r"[.'\" \\/]", "_", id)[0]

    def _find_match(self, line: str, patterns: List[Pattern]) -> Optional[str]:
        for pattern in patterns:
            matched = pattern.match(line)
            if matched:
                return matched[1]
        return None
