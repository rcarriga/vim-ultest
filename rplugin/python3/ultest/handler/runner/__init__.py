from typing import Optional, Set

from ...models import File, Namespace, Position, Result, Test, Tree
from ...vim_client import VimClient
from ..parsers import OutputParser, Position
from .processes import ProcessManager


class PositionRunner:
    """
    Handle running of tests and gathering results objects
    """

    def __init__(
        self,
        vim: VimClient,
        process_manager: ProcessManager,
        output_parser: OutputParser,
    ):
        self._vim = vim
        self._results = {}
        self._processes = process_manager
        self._output_parser = output_parser
        self._running: Set[str] = set()
        self._external_outputs = {}

    def run(self, tree: Tree[Position], file_name: str):
        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        if not self._output_parser.can_parse(runner) or len(tree) == 1:
            self._run_separately(tree)
            return
        self._run_group(tree, file_name)

    def register_external_start(self, tree: Tree[Position], output_path: str):
        self._vim.log.finfo(
            "Saving external stdout path '{output_path}' for test {process_id}"
        )
        self._external_outputs[tree.data.id] = output_path
        for pos in tree:
            self._register_started(pos)

    def register_external_result(self, tree: Tree[Position], code: int):
        file_name = tree.data.file
        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        path = self._external_outputs.pop(tree.data.id)
        self._vim.log.finfo(
            "Saving external result for process '{process_id}' with exit code {code}"
        )
        if not path:
            self._vim.log.error(
                f"No output path registered for position {tree.data.id}"
            )
            return
        self._process_results(tree=tree, code=code, output_path=path, runner=runner)

    def is_running(self, position_id: str) -> int:
        return int(position_id in self._running)

    def get_result(self, pos_id: str, file_name: str) -> Optional[Result]:
        return self._results.get((pos_id, file_name))

    def get_attach_script(self, process_id: str):
        return self._processes.create_attach_script(process_id)

    def _run_separately(self, tree: Tree[Position]):
        """
        Run a collection of tests. Each will be done in
        a separate thread.
        """
        root = self._vim.sync_call("get", "g:", "test#project_root") or None
        tests = []
        for pos in tree:
            if isinstance(pos, Test):
                tests.append(pos)

        for test in tests:
            self._register_started(test)
            cmd = self._vim.sync_call("ultest#adapter#build_cmd", test, "nearest")

            async def run(cmd=cmd, test=test):
                (code, output_path) = await self._processes.run(
                    cmd, test.file, test.id, cwd=root
                )
                self._register_result(
                    test,
                    Result(id=test.id, file=test.file, code=code, output=output_path),
                )

            self._vim.launch(run(), test.id)

    def _run_group(self, tree: Tree[Position], file_name: str):
        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        scope = "file" if isinstance(tree.data, File) else "nearest"
        cmd = self._vim.sync_call("ultest#adapter#build_cmd", tree[0], scope)
        root = self._vim.sync_call("get", "g:", "test#project_root") or None

        for pos in tree:
            self._register_started(pos)

        async def run(cmd=cmd):
            (code, output_path) = await self._processes.run(
                cmd, tree.data.file, tree.data.id, cwd=root
            )
            self._process_results(tree, code, output_path, runner)

        self._vim.launch(run(), file_name)

    def _process_results(
        self, tree: Tree[Position], code: int, output_path: str, runner: str
    ):
        namespaces = {
            position.id: position
            for position in tree
            if isinstance(position, Namespace)
        }
        output = []
        if code:
            with open(output_path, "r") as cmd_out:
                output = cmd_out.readlines()

        failed = {
            (failed.name, *failed.namespaces)
            for failed in self._output_parser.parse_failed(runner, output)
        }
        is_single = len(tree) == 1

        def get_code(pos: Position) -> int:
            if is_single:
                return code
            if not isinstance(pos, Test):
                return code
            # If none were parsed but the process failed then something else went wrong,
            # and we treat it as all failed
            if not failed:
                return code
            if (
                pos.name,
                *[namespaces[namespace_id].name for namespace_id in pos.namespaces],
            ) in failed:
                return code

            return 0

        for pos in tree:
            self._register_result(
                pos,
                Result(
                    id=pos.id,
                    file=pos.file,
                    code=get_code(pos) if code else 0,
                    output=output_path,
                ),
            )

    def _register_started(self, position: Position):
        self._vim.log.fdebug("Registering {position.id} as started")
        position.running = 1
        self._running.add(position.id)
        self._vim.call("ultest#process#start", position)

    def _register_result(self, position: Position, result: Result):
        self._vim.log.fdebug("Registering {position.id} as exited with result {result}")
        self._results[position.file, position.id] = result
        self._running.remove(position.id)
        self._vim.call("ultest#process#exit", position, result)
