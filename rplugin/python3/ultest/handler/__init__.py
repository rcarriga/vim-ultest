import os
from shlex import split
from typing import Callable, Dict, List, Optional, Tuple, Union

from pynvim import Nvim

from ..logging import UltestLogger
from ..models import File, Namespace, Test, Tree
from ..vim_client import VimClient
from .parsers import FileParser, OutputParser, Position
from .runner import PositionRunner, ProcessManager


class HandlerFactory:
    @staticmethod
    def create(vim: Nvim, logger: UltestLogger) -> "Handler":
        client = VimClient(vim, logger)
        file_parser = FileParser(client)
        process_manager = ProcessManager(client)
        output_parser = OutputParser(logger)
        runner = PositionRunner(
            vim=client, process_manager=process_manager, output_parser=output_parser
        )
        return Handler(client, file_parser=file_parser, runner=runner)


class Handler:
    def __init__(
        self,
        nvim: VimClient,
        file_parser: FileParser,
        runner: PositionRunner,
    ):
        self._vim = nvim
        self._runner = runner
        self._file_parser = file_parser
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

    def external_start(self, pos_id: str, file_name: str, stdout: str):
        tree = self._stored_positions.get(file_name)
        if not tree:
            self._vim.log.error(
                "Attempted to register started test for unknown file {file_name}"
            )
            raise ValueError(f"Unknown file {file_name}")

        position = tree.search(pos_id, lambda pos: pos.id)
        if not position:
            self._vim.log.error(
                f"Attempted to register unknown test as started {pos_id}"
            )
            return

        self._runner.register_external_start(position, stdout)

    def external_result(self, pos_id: str, file_name: str, exit_code: int):
        tree = self._stored_positions.get(file_name)
        if not tree:
            self._vim.log.error(
                "Attempted to register started test for unknown file {file_name}"
            )
            raise ValueError(f"Unknown file {file_name}")
        position = tree.search(pos_id, lambda pos: pos.id)
        if not position:
            self._vim.log.error(
                f"Attempted to register unknown test as started {pos_id}"
            )
            return
        self._runner.register_external_result(position, exit_code)

    def _present_output(self, result):
        if result.code and self._vim.sync_call("expand", "%") == result.file:
            self._vim.log.fdebug("Showing {result.id} output")
            line = self._vim.sync_call("getbufinfo", result.file)[0].get("lnum")
            nearest = self.get_nearest_position(line, result.file, strict=False)
            if nearest and nearest.data.id == result.id:
                self._vim.sync_call("ultest#output#open", result.dict())

    def run_nearest(self, line: int, file_name: str, update_empty: bool = True):
        """
        Run nearest test to cursor in file.

        If the line is 0 it will run the entire file.

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

        position = self.get_nearest_position(line, file_name, strict=False)

        if not position:
            return

        self._runner.run(position, file_name)

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

        self._runner.run(match, file_name)

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
            positions = await self._file_parser.parse_file_structure(
                file_name, vim_patterns
            )
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
        self, line: int, file_name: str, strict: bool
    ) -> Optional[Tree[Position]]:
        positions = self._stored_positions.get(file_name)
        if not positions:
            return None
        key = lambda pos: pos.line
        return positions.sorted_search(line, key=key, strict=strict)

    def get_nearest_test_dict(
        self, line: int, file_name: str, strict: bool
    ) -> Optional[Dict]:
        test = self.get_nearest_position(line, file_name, strict)
        if not test:
            return None
        return test.data.dict()

    def get_attach_script(self, process_id: str) -> Optional[Tuple[str, str]]:
        self._vim.log.finfo("Creating script to attach to process {process_id}")
        return self._runner.get_attach_script(process_id)

    def stop_test(self, pos_dict: Optional[Dict]):
        if not pos_dict:
            self._vim.log.fdebug("No process to cancel")
            return

        pos = self._parse_position(pos_dict)
        if not pos:
            self._vim.log.error(f"Invalid dict passed for position {pos_dict}")
            return

        self._runner.stop(pos, self._stored_positions[pos.file])

    def _parse_position(self, pos_dict: Dict) -> Optional[Position]:
        pos_type = pos_dict.get("type")
        if pos_type == "test":
            return Test(**pos_dict)
        if pos_type == "namespace":
            return Namespace(**pos_dict)
        if pos_type == "file":
            return File(**pos_dict)
        return None
