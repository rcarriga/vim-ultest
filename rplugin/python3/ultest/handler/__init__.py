import os
import json
import re
from shlex import split
from typing import Dict, List, Optional

from pynvim import Nvim

from .finder import TestFinder
from .results import ResultStore
from .runner import Runner
from ..models import Test, Test
from ..vim import VimClient, JobPriority


class HandlerFactory:
    @staticmethod
    def create(vim: Nvim) -> "Handler":
        client = VimClient(vim)
        finder = TestFinder(client)
        runner = Runner(client)
        results = ResultStore()
        return Handler(client, runner, finder, results)


class Handler:
    def __init__(
        self, nvim: VimClient, runner: Runner, finder: TestFinder, results: ResultStore
    ):
        self._vim = nvim
        self._runner = runner
        self._finder = finder
        self._results = results
        self._stored_tests: Dict[str, List[Test]] = {}
        self._prepare_env()

    def _prepare_env(self):
        rows = self._vim.sync_eval("g:ultest_output_rows")
        if rows:
            os.environ["ROWS"] = str(rows)
        elif "ROWS" in os.environ:
            os.environ.pop("ROWS")
        cols = self._vim.sync_eval("g:ultest_output_cols")
        if cols:
            os.environ["COLUMNS"] = str(cols)
        elif "COLUMNS" in os.environ:
            os.environ.pop("COLUMNS")

    def strategy(self, cmd: str):
        """
        Only meant to be called by vim-test.
        Acts as custom strategy.

        :param cmd: Command to run with file name, test name and line no appended.
        """

        custom_args = re.search(r"\[.*\]$", cmd)[0]  # type: ignore
        test_args = json.loads(bytes(json.loads(custom_args)).decode())
        command = split(cmd[: -len(custom_args)])
        test = Test(**test_args)

        def runner():
            result = self._runner.execute_test(command, test)
            test.running = 0
            self._results.add(test.file, result)
            self._vim.call("ultest#process#exit", test, result)
            self._vim.schedule(self._present_output, result)

        self._vim.launch(runner, test.line + 3)  # type: ignore

    def _present_output(self, result):
        if (
            result.code
            and self._vim.sync_eval("get(g:, 'ultest_output_on_run', 1)")
            and self._vim.sync_call("expand", "%") == result.file
        ):
            line = self._vim.sync_call("getbufinfo", result.file)[0].get("lnum")
            nearest = self.get_nearest_test(line, result.file, strict=False)
            if nearest and nearest.id == result.id:
                self._vim.sync_call("ultest#output#open", result.dict)

    def run_all(self, file_name: str):
        """
        Run all tests in a file.

        :param file_name: File to run in.
        """

        def runner():
            tests = self._stored_tests.get(file_name, [])
            self._runner.run_tests(tests)

        self._vim.launch(runner)

    def run_nearest(self, line: int, file_name: str):
        """
        Run nearest test to cursor in file.

        :param line: Line to run test nearest to.
        :param file_name: File to run in.
        """

        def runner():
            tests = self._stored_tests.get(file_name, [])
            test = self._finder.get_nearest_from(line, tests, strict=False)
            if test:
                self._runner.run_tests([test])

        self._vim.launch(runner)

    def run_single(self, test_id: str, file_name: str):
        """
        Run nearest test to cursor in file.

        :param test_id: Test to run
        :param file_name: File to run in.
        """

        def runner():
            tests = self._stored_tests.get(file_name, [])
            self._runner.run_tests([test for test in tests if test.id == test_id])

        self._vim.launch(runner)

    def update_positions(self, file_name: str, callback=None):
        """
        Check for new, moved and removed tests and send appropriate events.

        :param file_name: Name of file to clear results from.
        """

        recorded_tests = {
            test.id: test for test in self._stored_tests.get(file_name, [])
        }

        def runner(tests: List[Test]):
            self._stored_tests[file_name] = tests
            self._vim.call(
                "ultest#process#store_sorted_ids",
                file_name,
                [test.id for test in tests],
            )
            for test in tests:

                if recorded := recorded_tests.pop(test.id, None):
                    if recorded.line != test.line:
                        test.running = recorded.running
                        self._vim.call("ultest#process#move", test)
                elif existing_result := self._results.get(test.file, test.id):
                    self._vim.call("ultest#process#replace", test, existing_result)
                else:
                    self._vim.call("ultest#process#new", test)

            for removed in recorded_tests.values():
                self._vim.call("ultest#process#clear", removed)
            if callback:
                callback(tests)

        self._finder.find_all(file_name, runner, JobPriority.HIGH)

    def clear_all(self, file_name: str):
        """
        Clear all results from file and permanently delete the result file if exists.

        :param file_name: Name of file to clear results from.
        """

        def runner():
            tests = self._stored_tests.pop(file_name, [])
            for test in tests:
                result = self._results.pop(test.file, test.id)
                if result and result.code:
                    os.remove(result.output)

        self._vim.launch(runner)

    def get_nearest_test(
        self, line: int, file_name: str, strict: bool
    ) -> Optional[Test]:
        tests = self._stored_tests.get(file_name, [])
        test = self._finder.get_nearest_from(line, tests, strict)
        return test

    def get_nearest_test_dict(
        self, line: int, file_name: str, strict: bool
    ) -> Optional[Dict]:
        test = self.get_nearest_test(line, file_name, strict)
        return test and test.dict
