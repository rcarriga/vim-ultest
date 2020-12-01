from uuid import uuid4
from time import sleep
import tempfile
import os
import os.path
import subprocess
from typing import Iterable, List

from ..models import Position, Result, Test
from ..vim import VimClient


class Runner:
    """Handles scheduling and running tests."""

    def __init__(self, vim: VimClient):
        self._vim = vim

    def execute_test(self, cmd: List[str], test: Test) -> Result:
        """
        Runs a test with the given command and returns a result
        contstructed from the given test.

        :param cmd: Command arguments to run
        :type cmd: List[str]
        :param test: Test to build result from.
        :type test: Test
        :return: Result of test running.
        :rtype: Result
        """
        completed = subprocess.run(
            cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, check=False
        )
        if completed.returncode:
            (output_handle, output_path) = tempfile.mkstemp()
            with os.fdopen(output_handle, "w") as output_file:
                output_file.write(completed.stdout.decode())
        else:
            output_path = ""
        result_kwargs = {
            **test.dict,
            "code": completed.returncode,
            "output": output_path,
        }
        return Result(**result_kwargs)

    def run_positions(self, positions: Iterable[Position]):
        """
        Run a list of test positions. Each will be done in
        a separate thread.

        :param positions: Positions of tests.
        :type positions: Iterable[Position]
        """
        tests = [Test(**position.dict, id=str(uuid4())) for position in positions]
        for test in tests:
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)
            sleep(0.03)  # Minor sleep to avoid blocking main thread with IO
