import os
from typing import Callable, Dict, Optional

from ..models import Tree
from ..vim_client import VimClient
from .parsers import FileParser, Position
from .runner import PositionRunner


class PositionTracker:
    def __init__(
        self, vim: VimClient, file_parser: FileParser, runner: PositionRunner
    ) -> None:
        self._vim = vim
        self._file_parser = file_parser
        self._stored_positions: Dict[str, Tree[Position]] = {}
        self._runner = runner

    def update(self, file_name: str, callback: Optional[Callable] = None):
        """
        Check for new, moved and removed tests and send appropriate events.

        :param file_name: Name of file to clear results from.
        """

        if not os.path.isfile(file_name):
            return

        vim_patterns = self._get_file_patterns(file_name)
        if not vim_patterns:
            self._vim.log.fdebug("No patterns found for {file_name}")
            return

        recorded_tests: Dict[str, Position] = {
            test.id: test for test in self._stored_positions.get(file_name, [])
        }
        if not recorded_tests:
            self._init_test_file(file_name)

        self._vim.launch(
            self._async_update(file_name, vim_patterns, recorded_tests, callback),
            "update_positions",
        )

    async def _async_update(
        self,
        file_name: str,
        vim_patterns: Dict,
        recorded_tests: Dict[str, Position],
        callback: Optional[Callable],
    ):
        self._vim.log.finfo("Updating positions in {file_name}")

        positions = await self._parse_positions(file_name, vim_patterns)
        tests = list(positions)
        self._vim.call(
            "setbufvar",
            file_name,
            "ultest_sorted_tests",
            [test.id for test in tests],
        )
        for test in tests:
            if test.id in recorded_tests:
                recorded = recorded_tests.pop(test.id)
                if recorded.line != test.line:
                    test.running = self._runner.is_running(test.id)
                    self._vim.log.fdebug(
                        "Moving test {test.id} from {recorded.line} to {test.line} in {file_name}"
                    )
                    self._vim.call("ultest#process#move", test)
            else:
                existing_result = self._runner.get_result(test.id, test.file)
                if existing_result:
                    self._vim.log.fdebug(
                        "Replacing test {test.id} to {test.line} in {file_name}"
                    )
                    self._vim.call("ultest#process#replace", test, existing_result)
                else:
                    self._vim.log.fdebug("New test {test.id} found in {file_name}")
                    self._vim.call("ultest#process#new", test)

        self._remove_old_positions(recorded_tests)
        self._vim.command("doau User UltestPositionsUpdate")
        if callback:
            callback()

    def file_positions(self, file: str) -> Optional[Tree[Position]]:
        return self._stored_positions.get(file)

    def _init_test_file(self, file: str):
        self._vim.call("setbufvar", file, "ultest_results", {})
        self._vim.call("setbufvar", file, "ultest_tests", {})
        self._vim.call("setbufvar", file, "ultest_sorted_tests", [])
        self._vim.call("setbufvar", file, "ultest_file_structure", [])

    def _get_file_patterns(self, file: str) -> Dict:
        try:
            return self._vim.sync_call("ultest#adapter#get_patterns", file)
        except Exception:
            self._vim.log.exception(f"Error while evaluating patterns for file {file}")
            return {}

    async def _parse_positions(self, file: str, vim_patterns: Dict) -> Tree[Position]:
        positions = await self._file_parser.parse_file_structure(file, vim_patterns)
        self._stored_positions[file] = positions
        self._vim.call(
            "setbufvar",
            file,
            "ultest_file_structure",
            positions.map(lambda pos: {"type": pos.type, "id": pos.id}).to_list(),
        )
        return positions

    def _remove_old_positions(self, positions: Dict[str, Position]):
        if positions:
            self._vim.log.fdebug(
                "Removing tests {[recorded for recorded in recorded_tests]} from {file_name}"
            )
            for removed in positions.values():
                self._vim.call("ultest#process#clear", removed)
        else:
            self._vim.log.fdebug("No tests removed")
