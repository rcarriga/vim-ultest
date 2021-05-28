from collections import defaultdict
from functools import partial
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple

from ...models import File, Namespace, Position, Result, Test, Tree
from ...vim_client import VimClient
from ..parsers import OutputParser, ParseResult, Position
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
        self._results = defaultdict(dict)
        self._processes = process_manager
        self._output_parser = output_parser
        self._running: Set[str] = set()
        self._external_outputs = {}

    def run(
        self,
        tree: Tree[Position],
        file_tree: Tree[Position],
        file_name: str,
        on_start: Callable[[Position], None],
        on_finish: Callable[[Position, Result], None],
        env: Optional[Dict] = None,
    ):

        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        if not self._output_parser.can_parse(runner) or len(tree) == 1:
            self._run_separately(tree, on_start, on_finish, env)
            return
        self._run_group(tree, file_tree, file_name, on_start, on_finish, env)

    def stop(self, pos: Position, tree: Tree[Position]):
        root = None
        if self._vim.stop(pos.id):
            root = tree.search(pos.id, lambda data: data.id)
        else:
            for namespace in [*pos.namespaces, pos.file]:
                if self._vim.stop(namespace):
                    root = tree.search(namespace, lambda data: data.id)
                    break
        if not root:
            self._vim.log.warn(f"No matching job found for position {pos}")
            return

        for node in root:
            node.running = 0
            self._vim.call("ultest#process#move", node)

    def clear_results(self, file_name: str) -> Iterable[str]:
        return self._results.pop(file_name, {}).keys()

    def register_external_start(
        self,
        tree: Tree[Position],
        file_tree: Tree[Position],
        output_path: str,
        on_start: Callable[[Position], None],
    ):
        self._vim.log.finfo(
            "Saving external stdout path '{output_path}' for test {process_id}"
        )
        self._external_outputs[tree.data.id] = output_path
        for pos in tree:
            self._register_started(pos, on_start)

    def register_external_result(
        self,
        tree: Tree[Position],
        file_tree: Tree[Position],
        code: int,
        on_finish: Callable[[Position, Result], None],
    ):
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
        if not self._output_parser.can_parse(runner):
            for pos in tree:
                self._register_result(
                    pos,
                    result=Result(id=pos.id, file=pos.file, code=code, output=path),
                    on_finish=on_finish,
                )
            return
        self._process_results(
            tree=tree,
            file_tree=file_tree,
            code=code,
            output_path=path,
            runner=runner,
            on_finish=on_finish,
        )

    def is_running(self, position_id: str) -> int:
        return int(position_id in self._running)

    def get_result(self, pos_id: str, file_name: str) -> Optional[Result]:
        return self._results[file_name].get(pos_id)

    def get_attach_script(self, process_id: str):
        return self._processes.create_attach_script(process_id)

    def _run_separately(
        self,
        tree: Tree[Position],
        on_start: Callable[[Position], None],
        on_finish: Callable[[Position, Result], None],
        env: Optional[Dict] = None,
    ):
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
            self._register_started(test, on_start)
            cmd = self._vim.sync_call("ultest#adapter#build_cmd", test, "nearest")

            async def run(cmd=cmd, test=test):
                (code, output_path) = await self._processes.run(
                    cmd, test.file, test.id, cwd=root, env=env
                )
                self._register_result(
                    test,
                    Result(id=test.id, file=test.file, code=code, output=output_path),
                    on_finish,
                )

            self._vim.launch(run(), test.id)

    def _run_group(
        self,
        tree: Tree[Position],
        file_tree: Tree[Position],
        file_name: str,
        on_start: Callable[[Position], None],
        on_finish: Callable[[Position, Result], None],
        env: Optional[Dict] = None,
    ):
        runner = self._vim.sync_call("ultest#adapter#get_runner", file_name)
        scope = "file" if isinstance(tree.data, File) else "nearest"
        cmd = self._vim.sync_call("ultest#adapter#build_cmd", tree[0], scope)
        root = self._vim.sync_call("get", "g:", "test#project_root") or None

        for pos in tree:
            self._register_started(pos, on_start)

        async def run(cmd=cmd):
            (code, output_path) = await self._processes.run(
                cmd, tree.data.file, tree.data.id, cwd=root, env=env
            )
            self._process_results(tree, file_tree, code, output_path, runner, on_finish)

        self._vim.launch(run(), tree.data.id)

    def _process_results(
        self,
        tree: Tree[Position],
        file_tree: Tree[Position],
        code: int,
        output_path: str,
        runner: str,
        on_finish: Callable[[Position, Result], None],
    ):

        namespaces = {
            position.id: position
            for position in file_tree
            if isinstance(position, Namespace)
        }
        output = []
        if code:
            with open(output_path, "r") as cmd_out:
                output = cmd_out.readlines()

        parsed_failures = self._output_parser.parse_failed(runner, output)
        failed = self._get_failed_set(parsed_failures, tree)

        get_code = partial(self._get_exit_code, tree.data, code, failed, namespaces)

        for pos in tree:
            self._register_result(
                pos,
                Result(
                    id=pos.id,
                    file=pos.file,
                    code=get_code(pos) if code else 0,
                    output=output_path,
                ),
                on_finish,
            )

    def _get_exit_code(
        self,
        root: Position,
        group_code: int,
        failed: Set[Tuple[str, ...]],
        namespaces: Dict[str, Namespace],
        pos: Position,
    ):
        # If none were parsed but the process failed then something else went wrong,
        # and we treat it as all failed
        if not failed:
            return group_code
        if isinstance(root, Test):
            return group_code
        if isinstance(pos, File):
            return group_code
        if isinstance(pos, Namespace):
            namespace_names = tuple(
                namespaces[namespace_id].name
                for namespace_id in [*pos.namespaces, pos.id]
            )
            for failed_names in failed:
                if namespace_names == failed_names[1 : len(namespace_names) + 1]:
                    return group_code
            return 0

        if (
            pos.name,
            *[namespaces[namespace_id].name for namespace_id in pos.namespaces],
        ) in failed:
            return group_code

        return 0

    def _get_failed_set(
        self, parsed_failures: Iterator[ParseResult], tree: Tree[Position]
    ) -> Set[Tuple[str, ...]]:
        def from_root(namespaces: List[str]):
            for index, namespace in enumerate(namespaces):
                if namespace == tree.data.name:
                    return namespaces[index:]

            self._vim.log.warn(
                f"No namespaces found from root {tree.data.name} in parsed result {namespaces}"
            )
            return []

        return {
            (
                failed.name,
                *(
                    from_root(failed.namespaces)
                    if not isinstance(tree.data, File)
                    else failed.namespaces
                ),
            )
            for failed in parsed_failures
        }

    def _register_started(
        self, position: Position, on_start: Callable[[Position], None]
    ):
        self._vim.log.fdebug("Registering {position.id} as started")
        position.running = 1
        self._running.add(position.id)
        on_start(position)

    def _register_result(
        self,
        position: Position,
        result: Result,
        on_finish: Callable[[Position, Result], None],
    ):
        self._vim.log.fdebug("Registering {position.id} as exited with result {result}")
        self._results[position.file][position.id] = result
        self._running.remove(position.id)
        on_finish(position, result)
