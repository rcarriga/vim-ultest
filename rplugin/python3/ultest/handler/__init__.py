import os
from shlex import split
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from pynvim import Nvim

from ..logging import UltestLogger
from ..models import File, Namespace, Result, Test, Tree
from ..vim_client import VimClient
from .finder import Position, PositionFinder
from .parser import OutputParser
from .processes import ProcessManager
from .results import ResultStore


class HandlerFactory:
    @staticmethod
    def create(vim: Nvim, logger: UltestLogger) -> "Handler":
        client = VimClient(vim, logger)
        finder = PositionFinder(client)
        process_manager = ProcessManager(client)
        results = ResultStore()
        output_parser = OutputParser(logger)
        return Handler(client, process_manager, finder, results, output_parser)


class Handler:
    def __init__(
        self,
        nvim: VimClient,
        process_manager: ProcessManager,
        finder: PositionFinder,
        results: ResultStore,
        output_parser: OutputParser,
    ):
        self._vim = nvim
        self._process_manager = process_manager
        self._finder = finder
        self._results = results
        self._output_parser = output_parser
        self._stored_positions: Dict[str, Tree[Position]] = {}
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

    def safe_split(self, cmd: Union[str, List[str]]) -> List[str]:
        # Some runner position builders in vim-test don't split args properly (e.g. go test)
        return split(cmd if isinstance(cmd, str) else " ".join(cmd))

    def external_start(self, test_dict: Dict, stdout: str = ""):
        self._vim.log.fdebug(
            "External test {test_dict} registered with stdout {stdout}"
        )
        test = Test(**test_dict)
        self._register_started(test)
        if stdout:
            self._process_manager.register_external_output(test.id, stdout)

    def external_result(self, test_dict: Dict, exit_code: int, stdout: str = ""):
        test = Test(**test_dict)
        result = Result(id=test.id, file=test.file, code=exit_code, output=stdout)
        self._vim.log.fdebug("External test {test.id} result registered: {result}")
        self._process_manager.clear_external_output(test.id)
        self._register_result(test, result)

    def _run_tests(self, tests: Iterable[Test]):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        root = self._vim.sync_call("get", "g:", "test#project_root") or None
        for test in tests:
            self._vim.log.fdebug("Sending {test.id} to vim-test")
            self._register_started(test)
            cmd = self._vim.sync_call("ultest#adapter#build_cmd", test, "nearest")

            async def run(cmd=cmd, test=test):
                (code, output_path) = await self._process_manager.run(
                    cmd, test.file, test.id, cwd=root
                )
                self._register_result(
                    test,
                    Result(id=test.id, file=test.file, code=code, output=output_path),
                )

            self._vim.launch(run(), test.id)

    def _run_tree(self, tree: Tree[Position], file_name: str):
        tests = []
        namespaces = {}
        for position in tree:
            if isinstance(position, Test):
                tests.append(position)
            elif isinstance(position, Namespace):
                namespaces[position.id] = position

        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        if not tests:
            return

        if not self._output_parser.can_parse(runner) or len(tests) == 1:
            self._run_tests(tests)
            return

        scope = "file" if isinstance(tree.data, File) else "nearest"
        cmd = self._vim.sync_call("ultest#adapter#build_cmd", tree[0], scope)
        root = self._vim.sync_call("get", "g:", "test#project_root") or None
        for test in tests:
            self._register_started(test)

        async def run(cmd=cmd):
            (code, output_path) = await self._process_manager.run(
                cmd, tree.data.file, tree.data.id, cwd=root
            )
            output = []
            if code:
                with open(output_path, "r") as cmd_out:
                    output = cmd_out.readlines()
            failed = {
                (failed.name, *failed.namespaces)
                for failed in self._output_parser.parse_failed(runner, output)
            }

            def get_code(test: Test) -> int:
                if not code:
                    return 0
                # If none were parsed but the process failed then something else went wrong,
                # and we treat it as all failed
                if not failed:
                    return code
                if (
                    test.name,
                    *[
                        namespaces[namespace_id].name
                        for namespace_id in test.namespaces
                    ],
                ) in failed:
                    return code

                return 0

            for test in tests:
                self._register_result(
                    test,
                    Result(
                        id=test.id,
                        file=test.file,
                        code=get_code(test),
                        output=output_path,
                    ),
                )

        self._vim.launch(run(), file_name)

    def _register_started(self, test: Test):
        test.running = 1
        self._process_manager.register_new_process(test.id)
        self._vim.call("ultest#process#start", test)

    def _register_result(self, test: Test, result: Result):
        self._results.add(result.file, result)
        self._vim.call("ultest#process#exit", test, result)
        if self._show_on_run and result.output:
            self._vim.schedule(self._present_output, result)

    def _present_output(self, result):
        if result.code and self._vim.sync_call("expand", "%") == result.file:
            self._vim.log.fdebug("Showing {result.id} output")
            line = self._vim.sync_call("getbufinfo", result.file)[0].get("lnum")
            nearest = self.get_nearest_position(line, result.file, strict=False)
            if nearest and nearest.data.id == result.id:
                self._vim.sync_call("ultest#output#open", result.dict())

    def run_all(self, file_name: str, update_empty: bool = True):
        """
        Run all tests in a file.

        :param file_name: File to run in.
        """

        self._vim.log.finfo("Running all tests in {file_name}")
        positions = self._stored_positions.get(file_name)

        if not positions and update_empty:
            self._vim.log.finfo(
                "No tests found for {file_name}, rerunning after processing positions"
            )

            def run_after_update():
                self._vim.schedule(self.run_all, file_name, update_empty=False)

            self.update_positions(file_name, callback=run_after_update)

        if not positions:
            return

        self._run_tree(positions, file_name)

    def run_nearest(self, line: int, file_name: str, update_empty: bool = True):
        """
        Run nearest test to cursor in file.

        :param line: Line to run test nearest to.
        :param file_name: File to run in.
        """

        self._vim.log.finfo("Running nearest test in {file_name} at line {line}")
        positions = self._stored_positions.get(file_name)

        if not positions and update_empty:
            self._vim.log.finfo(
                "No tests found for {file_name}, rerunning after processing positions"
            )

            def run_after_update():
                self._vim.schedule(
                    self.run_nearest, line, file_name, update_empty=False
                )

            return self.update_positions(file_name, callback=run_after_update)

        position = self.get_nearest_position(
            line, file_name, strict=False, include_namespace=True
        )

        if not position:
            return

        self._run_tree(position, file_name)

    def run_single(self, test_id: str, file_name: str):
        """
        Run a test with the given ID

        :param test_id: Test to run
        :param file_name: File to run in.
        """
        self._vim.log.finfo("Running test {test_id} in {file_name}")
        positions = self._stored_positions.get(file_name)
        if not positions:
            return
        match = None
        for position in positions.nodes():
            if test_id == position.data.id:
                match = position

        if not match:
            return

        self._run_tree(match, file_name)

    def update_positions(self, file_name: str, callback: Optional[Callable] = None):
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
            test.id: test for test in self._stored_positions.get(file_name, [])
        }
        if not recorded_tests:
            self._vim.call("setbufvar", file_name, "ultest_results", {})
            self._vim.call("setbufvar", file_name, "ultest_tests", {})
            self._vim.call("setbufvar", file_name, "ultest_sorted_tests", [])
            self._vim.call("setbufvar", file_name, "ultest_file_structure", [])

        async def runner():
            self._vim.log.finfo("Updating positions in {file_name}")
            positions = await self._finder.find_all(file_name, vim_patterns)
            self._stored_positions[file_name] = positions
            self._vim.call(
                "setbufvar",
                file_name,
                "ultest_file_structure",
                positions.map(lambda pos: {"type": pos.type, "id": pos.id}).to_list(),
            )

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
                        if isinstance(test, Test):
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
                    "Removing tests {[recorded for recorded in recorded_tests]} from {file_name}"
                )
                for removed in recorded_tests.values():
                    self._vim.call("ultest#process#clear", removed)
            else:
                self._vim.log.fdebug("No tests removed")
            self._vim.command("doau User UltestPositionsUpdate")
            if callback:
                callback()

        self._vim.launch(runner(), "update_positions")

    def get_nearest_position(
        self, line: int, file_name: str, strict: bool, include_namespace: bool = False
    ) -> Optional[Tree[Position]]:
        positions = self._stored_positions.get(file_name)
        if not positions:
            return None
        key = (
            (lambda pos: pos.line)
            if include_namespace
            else lambda pos: pos.line
            if isinstance(pos, Test)
            else -1
        )
        return positions.sorted_search(line, key=key, strict=strict)

    def get_nearest_test_dict(
        self, line: int, file_name: str, strict: bool, include_namespace: bool = False
    ) -> Optional[Dict]:
        test = self.get_nearest_position(line, file_name, strict, include_namespace)
        if not test:
            return None
        return test.data.dict()

    def get_attach_script(self, process_id: str) -> Optional[Tuple[str, str]]:
        self._vim.log.finfo("Creating script to attach to process {process_id}")
        return self._process_manager.create_attach_script(process_id)

    def stop_test(self, test_dict: Optional[Dict]):
        if not test_dict:
            self._vim.log.fdebug("No test to cancel")
            return
        test = Test(**test_dict)
        self._vim.log.finfo("Stopping all jobs for test {test.id}")
        self._vim.stop(test.id)
        test.running = 0
        self._vim.call("ultest#process#move", test)
