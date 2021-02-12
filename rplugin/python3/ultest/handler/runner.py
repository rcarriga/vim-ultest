import logging
import os
import tempfile
from asyncio import subprocess
from contextlib import contextmanager
from io import BufferedReader, BufferedWriter
from os import path
from threading import Event, Thread
from typing import Dict, Iterable, Iterator, List, Tuple

from ..models import Result, Test
from ..vim import VimClient


class TestProcess:
    def __init__(self, in_path: str, out_path: str):
        self._in_path = in_path
        self._out_path = out_path
        self._close_event = Event()
        self._create_stdin()
        self._wipe_stdout()

    def _create_stdin(self):
        if os.path.exists(self._in_path):
            os.remove(self._in_path)
        os.mkfifo(self._in_path, 0o777)

    def _wipe_stdout(self):
        if os.path.exists(self._out_path):
            os.remove(self._out_path)

    def _keep_stdin_open(self):
        def keep_open():
            with open(self._in_path, "wb"):
                self._close_event.wait()
                self._close_event.clear()

        Thread(target=keep_open).start()

    @contextmanager
    def open(self) -> Iterator[Tuple[BufferedReader, BufferedWriter]]:
        in_handle = self._open_stdin()
        out_handle = self._open_stdout()
        try:
            yield (in_handle, out_handle)
        finally:
            self._close_stdin(in_handle)
            self._close_stdout(out_handle)

    def _open_stdin(self) -> BufferedReader:
        if self._close_event.is_set():
            raise IOError(f"Handle is already open for {self._in_path}")
        self._keep_stdin_open()
        return open(self._in_path, "rb")

    def _close_stdin(self, reader: BufferedReader):
        self._close_event.set()
        reader.close()

    def _close_stdout(self, writer: BufferedWriter):
        writer.close()

    def _open_stdout(self) -> BufferedWriter:
        return open(self._out_path, "wb")


class ProcessManager:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim
        self._dir = tempfile.TemporaryDirectory(prefix="ultest")
        self._processes: Dict[str, TestProcess] = {}

    def _test_file_dir(self, file: str) -> str:
        return os.path.join(self._dir.name, file.replace(os.path.pathsep, "__"))

    def _create_test_file_dir(self, file: str):
        path = self._test_file_dir(file)
        if not os.path.isdir(path):
            os.mkdir(path)

    def stdin_name(self, test: Test) -> str:
        return path.join(self._test_file_dir(test.file), f"{test.id}_in")

    def stdout_name(self, test: Test) -> str:
        return path.join(self._test_file_dir(test.file), f"{test.id}_out")

    async def run(self, cmd: List[str], test: Test):
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :param test: Test to build result from.
        :return: Result of test running.
        :rtype: Result
        """

        self._create_test_file_dir(test.file)
        stdin_path = self.stdin_name(test)
        stdout_path = self.stdout_name(test)
        test_process = TestProcess(in_path=stdin_path, out_path=stdout_path)
        self._processes[test.id] = test_process
        with test_process.open() as (in_handle, out_handle):
            logging.error(f"{in_handle} {out_handle}")
            process = await subprocess.create_subprocess_exec(
                *cmd, stdin=in_handle, stderr=out_handle, stdout=out_handle
            )
            code = await process.wait()
            result = Result(id=test.id, file=test.file, code=code, output=stdout_path)
            del self._processes[test.id]
            return result

    async def run_tests(self, tests: Iterable[Test]):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        for test in tests:
            test.running = 1
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)

    def clear(self):
        self._dir.cleanup()
