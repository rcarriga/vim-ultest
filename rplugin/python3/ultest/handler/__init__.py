import json
import re
from shlex import split
from typing import Dict, List

from pynvim import Nvim

from ultest.handler.positions import Positions
from ultest.handler.results import Results
from ultest.handler.runner import Runner
from ultest.models import Position, Result, Test
from ultest.processors import Processors
from ultest.vim import VimClient


class Handler:
    def __init__(
        self, nvim: VimClient, runner: Runner, positions: Positions, results: Results
    ):
        self._vim = nvim
        self._runner = runner
        self._positions = positions
        self._results = results

    def strategy(self, cmd: str):
        """
        Only meant to be called by vim-test.
        Acts as custom strategy.

        :param cmd: Command to run with file name, test name and line no appended.
        :type cmd: str
        """
        custom_args = re.search(r"\[.*\]$", cmd)[0]  # type: ignore
        test_args = json.loads(bytes(json.loads(custom_args)).decode())
        command = split(cmd[: -len(custom_args)])
        test = Test(**test_args)
        self._vim.launch(self.runner, command, test)

    def runner(self, cmd: List[str], test: Test):
        result = self._runner.test(cmd, test)
        self._results.handle(result)
        self._vim.schedule(self._present_output, result)

    def _present_output(self, result):
        if result.code and self._vim.sync_eval("get(g:, 'ultest_output_on_run', 1)"):
            nearest = self._positions.nearest_stored(result.file, False)
            if nearest and nearest.name == result.name:
                self._vim.sync_call("ultest#output#open", result.output)

    def run_all(self, file_name: str):
        """
        Run all tests in a file.

        :param file_name: File to run in.
        :type file_name: str
        """
        self._positions.get_all(file_name, self._runner.positions)

    def run_nearest(self, file_name: str):
        """
        Run nearest test to cursor in file.

        :param file_name: File to run in.
        :type file_name: str
        """

        def runner(position):
            self._runner.positions([position])

        self._positions.get_nearest(file_name, runner, False)

    def clear_old(self, file_name: str):
        """
        Check for removed tests and clear results from processors.

        :param file_name: Name of file to clear results from.
        :type file_name: str
        """

        def runner(positions):
            self._results.clear_old(file_name, positions)

        self._positions.get_all(file_name, runner)

    def store_positions(self, file_name: str):
        """Update and store the test positions for a buffer.

        :param file_name: File to update positions in.
        :type file_name: str
        """
        self._positions.get_all(file_name)

    def get_positions(self, file_name: str) -> Dict[str, Dict]:
        """Get the known positions for a buffer, mapped by name.

        :param file_name: File to get positions from.
        :type file_name: str
        """
        return {
            position.name: position.dict
            for position in self._positions.all_stored(file_name)
        }

    def nearest_output(self, file_name: str, strict: bool) -> str:
        """
        Get the output of the nearest result.

        :param file_name: File to open result from.
        :type file_name: str
        :param strict: If true then only open when current line == line test is defined
        :type strict: bool
        :return: Path to output file
        :rtype: str
        """
        position = self._positions.nearest_stored(file_name, strict)
        return self._results.output(file_name, position.name) if position else ""

    def get_output(self, file_name: str, test_name: str) -> str:
        """Get the output of a test.

        :param file_name: Name of file to get result from.
        :type file_name: str
        :param test_name: Name of test to get output for.
        :type test_name: str
        :return: Path to output file
        :rtype: str
        """
        return self._results.output(file_name, test_name)


def create(vim: Nvim) -> Handler:
    client = VimClient(vim)
    processors = Processors(client)
    positions = Positions(client)
    runner = Runner(client, processors)
    results = Results(client, processors)
    return Handler(client, runner, positions, results)
