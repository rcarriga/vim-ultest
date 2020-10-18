import re
from typing import Callable, Dict, List, Optional, Iterable
from itertools import tee, zip_longest

from ultest.models import Position
from ultest.vim import VimClient


class Positions:
    def __init__(self, vim: VimClient):
        self._vim = vim
        self._positions: Dict[str, List[Position]] = {}
        self._last_runs: Dict[str, List[Positions]] = {}

    def all_stored(self, file_name: str) -> List[Position]:
        """
        Get the last known test positions for a file.
        Can be run on main thread.

        :param file_name: Name of file to check.
        :type file_name: str
        :rtype: Dict[str, Position]
        """
        return self._positions.get(file_name, [])

    def get_all(
        self, file_name: str, receiver: Callable[[Iterable[Position]], None] = None
    ):
        """
        Calculate the test positions of a file and supply the result to a callback.
        This will also update the stored positions.
        Must be started on main Vim thread.
        The receiver will be started on a seperate thread.

        :param file_name: Name of file to get positions of
        :type file_name: str
        :param receiver: Function to supply result to.
        :type receiver: Callable[[Iterable[Position]], None]
        """
        patterns = self._vim.test.patterns(file_name)
        if patterns:
            lines = self._vim.buffers.contents(file_name)

            def runner():
                positions = self._calculate_positions(file_name, patterns, lines)

                to_send, to_store = tee(positions)
                self._vim.launch(self._store_positions, file_name, to_store)
                if receiver:
                    receiver(to_send)

            self._vim.launch(runner)

    def nearest_stored(self, file_name: str, strict: bool) -> Optional[Position]:
        """
        Get the nearest position from the last known positions.
        The nearest position is the first position found above the cursor.

        :param file_name: File to get position from.
        :type file_name: str
        :param strict: Only return position if on current line.
        :type strict: bool
        :return: Position closest to cursor.
        :rtype: Optional[Position]
        """
        current_line = self._vim.buffers.current_line(file_name)
        positions = self.all_stored(file_name)
        if not positions:
            return None
        first_test_line = positions[0].line
        offset = current_line - first_test_line
        if offset < 0:
            return None
        nearest = positions[offset] if offset < len(positions) else positions[-1]
        return nearest if nearest.line == current_line or not strict else None

    def get_nearest(
        self,
        file_name: str,
        receiver: Callable[[Optional[Position]], None],
        strict: bool,
    ):
        """
        Calculate all the positions in a file and et the nearest.
        The nearest position is the first position found above the cursor.
        This will also update the stored positions.

        :param file_name: File to get position from.
        :type file_name: str
        :param strict: Only return position if on current line.
        :type strict: bool
        :param receiver: Function to receive positions.
        :type receiver: Callable[[Optional[Position]], None]
        """
        current_line = self._vim.buffers.current_line(file_name)

        def runner(positions):
            nearest = self._nearest(positions, current_line, strict)
            if nearest:
                receiver(nearest)

        self.get_all(file_name, runner)

    def _nearest(self, positions: Iterable[Position], current_line: int, strict: bool):
        last = None
        for nearest in positions:
            if nearest.line == current_line:
                return nearest
            if last and last.line < current_line < nearest.line:
                return None if strict else last
            last = nearest
        if not strict and last and last.line < current_line:
            return last
        return None

    def _store_positions(self, file_name: str, positions: Iterable[Position]):
        positions = list(positions)
        if positions:
            future_positions = positions[1:]
            pos_list = []
            for current, next_pos in zip_longest(positions, future_positions):
                next_line = next_pos.line if next_pos else current.line + 1
                for position in (next_line - current.line) * [current]:
                    pos_list.append(position)
            self._positions[file_name] = pos_list

    def _calculate_positions(
        self,
        file_name: str,
        patterns: Dict,
        lines: List[str],
        is_reversed: bool = False,
    ) -> Iterable[Position]:
        last_position = None
        num_lines = len(lines)
        for line_index, line in enumerate(lines):
            test_name = self._find_test_name(line, patterns["test"])
            if test_name and last_position != test_name:
                last_position = test_name
                line_no = num_lines - line_index if is_reversed else line_index + 1
                yield Position(file=file_name, line=line_no, col=1, name=test_name)

    def _find_test_name(self, line: str, patterns: List[str]) -> Optional[str]:
        matches: List[str] = []
        for pattern in patterns:
            matched = re.match(pattern, line)
            matches = matches + list(matched.groups()) if matched else []
        return matches[0] if matches else None
