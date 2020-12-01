import re
from typing import Callable, Dict, List, Optional
from time import sleep

from ..models import Position
from ..vim import VimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}


class Positions:
    def __init__(self, vim: VimClient):
        self._vim = vim
        self._positions: Dict[str, List[Position]] = {}

    def get_stored(self, file_name: str) -> List[Position]:
        return self._positions.get(file_name, [])

    def calculate_all(
        self, file_name: str, receiver: Callable[[List[Position]], None] = None
    ):
        vim_patterns = self._vim.sync_call("ultest#adapter#get_patterns", file_name)

        def runner():
            patterns = self._convert_patterns(vim_patterns)
            with open(file_name, "r") as test_file:
                lines = test_file.readlines()
            positions = self._calculate_positions(file_name, patterns, lines)
            self._positions[file_name] = positions
            if receiver:
                receiver(positions)

        self._vim.launch(runner)

    def _convert_patterns(self, vim_patterns: Dict[str, List[str]]):
        return [
            self._convert_regex(pattern) for pattern in vim_patterns.get("test", "")
        ]

    def _convert_regex(self, vim_regex: str) -> str:
        regex = vim_regex
        for pattern, repl in REGEX_CONVERSIONS.items():
            regex = re.sub(pattern, repl, regex)
        return regex

    def get_nearest_stored(self, file_name: str, strict: bool) -> Optional[Position]:
        current_line = self._vim.sync_call("getbufinfo", file_name)[0].get("lnum")
        positions = self.get_stored(file_name)
        return self._get_nearest_from(positions, current_line, strict)

    def calculate_nearest(
        self,
        file_name: str,
        receiver: Callable[[Optional[Position]], None],
        strict: bool,
    ):
        current_line = self._vim.sync_call("getbufinfo", file_name)[0].get("lnum")

        def runner(positions):
            nearest = self._get_nearest_from(positions, current_line, strict)
            if nearest:
                receiver(nearest)

        self.calculate_all(file_name, runner)

    def _get_nearest_from(
        self, positions: List[Position], current_line: int, strict: bool
    ):
        l = 0
        r = len(positions) - 1
        while l <= r:
            m = int((l + r) / 2)
            mid = positions[m]
            if mid.line < current_line:
                l = m + 1
            elif mid.line > current_line:
                r = m - 1
            else:
                return mid
        return positions[r] if not strict and len(positions) > r else None

    def _calculate_positions(
        self,
        file_name: str,
        patterns: List[str],
        lines: List[str],
    ) -> List[Position]:
        positions = []
        for line_index, line in enumerate(lines):
            test_name = self._find_test_name(line, patterns)
            if test_name:
                line_no = line_index + 1
                positions.append(
                    Position(file=file_name, line=line_no, col=1, name=test_name)
                )
        return positions

    def _find_test_name(self, line: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            matched = re.match(pattern, line)
            if matched:
                return matched[1]
        return None
