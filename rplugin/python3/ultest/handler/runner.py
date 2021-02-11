import tempfile
from asyncio import subprocess
from typing import Iterable, List

from ..models import Result, Test
from ..vim import VimClient


class Runner:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim

    async def execute_test(self, cmd: List[str], test: Test):
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :param test: Test to build result from.
        :return: Result of test running.
        :rtype: Result
        """

        (output_handle, output_path) = tempfile.mkstemp()
        with open(output_handle, "wb+") as handle:
            completed = subprocess.create_subprocess_exec(
                *cmd, stdin=handle, stderr=handle, stdout=handle
            )
            process = await completed
            code = await process.wait()
            return Result(
                id=test.id,
                file=test.file,
                code=code,
                output=output_path,
            )

    async def run_tests(self, tests: Iterable[Test]):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        for test in tests:
            test.running = 1
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)
