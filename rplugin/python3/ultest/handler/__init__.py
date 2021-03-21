import os
from shlex import split
from typing import Dict, List, Optional, Tuple

from pynvim import Nvim

from ..logging import UltestLogger
from ..models import Result, Test
from ..vim_client import VimClient
from .finder import TestFinder
from .processes import ProcessManager
from .results import ResultStore


class HandlerFactory:
    @staticmethod
    def create(vim: Nvim, logger: UltestLogger) -> "Handler":
        client = VimClient(vim, logger)
        finder = TestFinder(client)
        process_manager = ProcessManager(client)
        results = ResultStore()
        return Handler(client, process_manager, finder, results)


class Handler:
    def __init__(
        self,
        nvim: VimClient,
        process_manager: ProcessManager,
        finder: TestFinder,
        results: ResultStore,
    ):
        self._vim = nvim
        self._process_manager = process_manager
        self._finder = finder
        self._results = results
        self._stored_tests: Dict[str, List[Test]] = {}
        self._prepare_env()
        self._show_on_run = self._vim.sync_eval("get(g:, 'ultest_output_on_run', 1)")
        self._vim.log.debug("Handler created")

    def _prepare_env(self):
        rows = self._vim.sync_eval("g:ultest_output_rows")
        if rows:
            self._vim.log.debug(f"Setting ROWS to {rows}")
            os.environ["ROWS"] = str(rows)
        elif "ROWS" in os.environ:
            self._vim.log.debug("Clearing ROWS value")
            os.environ.pop("ROWS")
        cols = self._vim.sync_eval("g:ultest_output_cols")
        if cols:
            self._vim.log.debug(f"Setting COLUMNS to {cols}")
            os.environ["COLUMNS"] = str(cols)
        elif "COLUMNS" in os.environ:
            self._vim.log.debug("Clearing COLUMNS value")
            os.environ.pop("COLUMNS")

    def strategy(self, cmd: List, test_dict: Dict):
        test = Test(**test_dict)
        self._vim.log.fdebug("Received test from vim-test {test.id} with args {cmd}")

        async def runner():
            # Some runner position builders in vim-test don't split args properly (e.g. go test)
            safe_cmd = split(" ".join(cmd))
            result = await self._process_manager.run(safe_cmd, test)
            test.running = 0
            self._register_result(test, result)

        self._vim.launch(runner(), test.id)

    def external_result(self, test_dict: Dict, exit_code: int, stdout: str = ""):
        test = Test(**test_dict)
        result = Result(id=test.id, file=test.file, code=exit_code, output=stdout)
        self._register_result(test, result)

    def _register_started(self, test_dict: Dict):
        self._vim.call

    def _register_result(self, test: Test, result: Result):
        self._results.add(result.file, result)
        self._vim.call("ultest#process#exit", test, result)
        if self._show_on_run and result.output:
            self._vim.schedule(self._present_output, result)

    def _present_output(self, result):
        if result.code and self._vim.sync_call("expand", "%") == result.file:
            self._vim.log.fdebug("Showing {result.id} output")
            line = self._vim.sync_call("getbufinfo", result.file)[0].get("lnum")
            nearest = self.get_nearest_test(line, result.file, strict=False)
            if nearest and nearest.id == result.id:
                self._vim.sync_call("ultest#output#open", result.dict())

    def run_all(self, file_name: str):
        """
        Run all tests in a file.

        :param file_name: File to run in.
        """

        async def run():
            self._vim.log.finfo("Running all tests in {file_name}")
            tests = self._stored_tests.get(file_name, [])
            await self._process_manager.run_tests(tests)

        self._vim.launch(run(), "run_all")

    def run_nearest(self, line: int, file_name: str):
        """
        Run nearest test to cursor in file.

        :param line: Line to run test nearest to.
        :param file_name: File to run in.
        """

        self._vim.log.finfo("Running nearest test in {file_name} at line {line}")
        tests = self._stored_tests.get(file_name, [])
        test = self._finder.get_nearest_from(line, tests, strict=False)
        if test:

            async def run():
                self._vim.log.finfo("Nearest test found is {test.id}")
                await self._process_manager.run_tests([test])  # type: ignore

            self._vim.launch(run(), test.id)

    def run_single(self, test_id: str, file_name: str):
        """
        Run nearest test to cursor in file.

        :param test_id: Test to run
        :param file_name: File to run in.
        """

        async def run():
            self._vim.log.finfo("Running test {test_id} in {file_name}")
            tests = self._stored_tests.get(file_name, [])
            await self._process_manager.run_tests(
                [test for test in tests if test.id == test_id]
            )

        self._vim.launch(run(), test_id)

    def update_positions(self, file_name: str):
        """
        Check for new, moved and removed tests and send appropriate events.

        :param file_name: Name of file to clear results from.
        """

        if not os.path.isfile(file_name):
            return
        try:
            vim_patterns = self._vim.sync_call("ultest#adapter#get_patterns", file_name)
        except Exception:
            self._vim.log.exception(
                f"Error whilte evaluating patterns for file {file_name}"
            )
            return
        if not vim_patterns:
            self._vim.log.fdebug("No patterns found for {file_name}")
            return

        recorded_tests = {
            test.id: test for test in self._stored_tests.get(file_name, [])
        }
        if not recorded_tests:
            self._vim.call("setbufvar", file_name, "ultest_results", {})
            self._vim.call("setbufvar", file_name, "ultest_tests", {})
            self._vim.call("setbufvar", file_name, "ultest_sorted_tests", [])

        async def runner():
            self._vim.log.finfo("Updating positions in {file_name}")
            tests = await self._finder.find_all(file_name, vim_patterns)
            self._stored_tests[file_name] = tests
            self._vim.call(
                "ultest#process#store_sorted_ids",
                file_name,
                [test.id for test in tests],
            )
            for test in tests:
                if test.id in recorded_tests:
                    recorded = recorded_tests.pop(test.id)
                    if recorded.line != test.line:
                        test.running = self._process_manager.is_running(test.id)
                        self._vim.log.fdebug(
                            "Moving test {test.id} from {recorded.line} to {test.line} in {file_name}"
                        )
                        self._vim.call("ultest#process#move", test)
                else:
                    existing_result = self._results.get(test.file, test.id)
                    if existing_result:
                        self._vim.log.fdebug(
                            "Replacing test {test.id} to {test.line} in {file_name}"
                        )
                        self._vim.call("ultest#process#replace", test, existing_result)
                    else:
                        self._vim.log.fdebug("New test {test.id} found in {file_name}")
                        self._vim.call("ultest#process#new", test)

            if recorded_tests:
                self._vim.log.fdebug(
                    "Removing tests {[recorded.id for recorded in recorded_tests]} from {file_name}"
                )
                for removed in recorded_tests.values():
                    self._vim.call("ultest#process#clear", removed)
            else:
                self._vim.log.fdebug("No tests removed")
            self._vim.command("doau User UltestPositionsUpdate")

        self._vim.launch(runner(), "update_positions")

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
        return test and test.dict()

    def get_attach_script(self, test_id: str) -> Optional[Tuple[str, str]]:
        self._vim.message("heleele")
        self._vim.log.finfo("Creating script to attach to test {test_id}")
        return self._process_manager.create_attach_script(test_id)

    def stop_test(self, test_dict: Optional[Dict]):
        if not test_dict:
            self._vim.log.fdebug("No test to cancel")
            return
        test = Test(**test_dict)
        self._vim.log.finfo("Stopping all jobs for test {test.id}")
        self._vim.stop(test.id)
        test.running = 0
        self._vim.call("ultest#process#move", test)
