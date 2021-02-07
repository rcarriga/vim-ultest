import tempfile
import os
import os.path
import subprocess
from typing import Iterable, List

from ..models import Result, Test
from ..vim import VimClient


class Runner:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim

    def execute_test(self, cmd: List[str], test: Test) -> Result:
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :param test: Test to build result from.
        :return: Result of test running.
        :rtype: Result
        """
        completed = subprocess.run(
            cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, check=False
        )
        if completed.returncode:
            (output_handle, output_path) = tempfile.mkstemp()
            with os.fdopen(output_handle, "wb") as output_file:
                output_file.write(completed.stdout)
        else:
            output_path = ""
        return Result(
            id=test.id, file=test.file, code=completed.returncode, output=output_path
        )

    def run_tests(self, tests: Iterable[Test]):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        for test in tests:
            test.running = 1
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)
