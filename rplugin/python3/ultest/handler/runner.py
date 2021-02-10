import tempfile
from asyncio import run, subprocess
from typing import Any, Callable, Iterable, List

from ..models import Result, Test
from ..vim import VimClient


class Runner:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim

    def execute_test(
        self, cmd: List[str], test: Test, receiver: Callable[[Result], Any]
    ):
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :param test: Test to build result from.
        :return: Result of test running.
        :rtype: Result
        """

        async def handle_test():
            (output_handle, output_path) = tempfile.mkstemp()
            with open(output_handle, "wb+") as handle:
                completed = subprocess.create_subprocess_exec(
                    *cmd, stdin=handle, stderr=handle, stdout=handle
                )
                process = await completed
                await process.wait()
                res = Result(
                    id=test.id,
                    file=test.file,
                    code=process.returncode,
                    output=output_path,
                )
                receiver(res)

        run(handle_test())

    def run_tests(self, tests: Iterable[Test]):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        for test in tests:
            test.running = 1
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)
