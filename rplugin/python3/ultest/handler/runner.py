import tempfile
import os
import os.path
import random
import subprocess
from typing import Iterable, List, Dict

from ultest.models import Position, Result, Test
from ultest.processors import Processors
from ultest.vim import VimClient


class Runner:
    """Handles scheduling and running tests."""

    def __init__(self, vim: VimClient, processor: Processors):
        self._vim = vim
        self._processor = processor

    def test(self, cmd: List[str], test: Test) -> Result:
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
        (output_handle, output_path) = tempfile.mkstemp()
        with os.fdopen(output_handle, "w") as output_file:
            output_file.write(completed.stdout.decode())
        result_kwargs: Dict = {
            **test.dict,
            "code": completed.returncode,
            "output": output_path,
        }
        return Result(**result_kwargs)

    def positions(self, positions: Iterable[Position]):
        """
        Run a list of test positions. Each will be done in
        a separate thread.

        :param positions: Positions of tests.
        :type positions: Iterable[Position]
        """
        for position in positions:
            self._vim.schedule(self._run_position, position)

    def _run_position(self, position: Position):
        test_id = random.randint(1000, 1000000)
        test_kwargs: Dict = {**position.dict, "id": test_id}
        test = Test(**test_kwargs)
        self._processor.start(test)
        self._vim.test.run(test)
