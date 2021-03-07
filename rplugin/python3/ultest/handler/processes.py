import inspect
import os
import re
import tempfile
from asyncio import subprocess, CancelledError
from contextlib import contextmanager
from io import BufferedReader, BufferedWriter
from os import path
from threading import Event, Thread
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from ..logging import UltestLogger
from ..models import Result, Test
from ..vim_client import VimClient


class TestProcess:
    def __init__(self, in_path: str, out_path: str, logger: UltestLogger):
        self.in_path = in_path
        self.out_path = out_path
        self._logger = logger
        self._close_event = Event()
        self._create_stdin()
        self._wipe_stdout()
        self.process: Optional[subprocess.Process] = None

    def _create_stdin(self):
        if os.path.exists(self.in_path):
            os.remove(self.in_path)
        os.mkfifo(self.in_path, 0o777)

    def _wipe_stdout(self):
        if os.path.exists(self.out_path):
            os.remove(self.out_path)

    def _keep_stdin_open(self):
        def keep_open():
            with open(self.in_path, "wb"):
                self._close_event.wait()
                self._close_event.clear()

        Thread(target=keep_open).start()

    @contextmanager
    def open(self) -> Iterator[Tuple[BufferedReader, BufferedWriter]]:
        in_handle = self._open_stdin()
        out_handle = self._open_stdout()
        try:
            yield (in_handle, out_handle)
        except:
            self._logger.exception("Exception while open")
            raise
        finally:
            self._close_stdin(in_handle)
            self._close_stdout(out_handle)

    def _open_stdin(self) -> BufferedReader:
        if self._close_event.is_set():
            raise IOError(f"Handle is already open for {self.in_path}")
        self._keep_stdin_open()
        return open(self.in_path, "rb")

    def _close_stdin(self, reader: BufferedReader):
        self._close_event.set()
        reader.close()
        if os.path.exists(self.in_path):
            os.remove(self.in_path)

    def _close_stdout(self, writer: BufferedWriter):
        writer.close()

    def _open_stdout(self) -> BufferedWriter:
        return open(self.out_path, "wb")


class ProcessManager:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim
        self._dir = tempfile.TemporaryDirectory(prefix="ultest")
        self._processes: Dict[str, Optional[TestProcess]] = {}

    def _test_file_dir(self, file: str) -> str:
        return os.path.join(
            self._dir.name, re.subn(r"[.'\" \\/]", "_", file.replace(os.sep, "__"))[0]
        )

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
        test_process = TestProcess(
            in_path=stdin_path, out_path=stdout_path, logger=self._vim.log
        )
        self._processes[test.id] = test_process
        self._vim.log.fdebug("Starting test process {test.id} with command: {cmd}")
        try:
            async with self._vim.semaphore:
                with test_process.open() as (in_handle, out_handle):
                    try:
                        process = await subprocess.create_subprocess_exec(
                            *cmd, stdin=in_handle, stderr=out_handle, stdout=out_handle
                        )
                    except CancelledError:
                        raise
                    except Exception:
                        self._vim.log.warn(
                            f"An exception was thrown when starting test {test.id}",
                            exc_info=True,
                        )
                        code = 1
                    else:
                        test_process.process = process
                        code = await process.wait()
                    self._vim.log.fdebug(
                        "Test {test.id} complete with exit code: {code}"
                    )
                    result = Result(
                        id=test.id, file=test.file, code=code, output=stdout_path
                    )
                    return result
        finally:
            del self._processes[test.id]

    async def run_tests(
        self, tests: Iterable[Test]
    ):
        """
        Run a list of tests. Each will be done in
        a separate thread.
        """
        for test in tests:
            self._vim.log.fdebug("Sending {test.id} to vim-test with runner {runner}")
            test.running = 1
            self._processes[test.id] = None
            self._vim.call("ultest#process#start", test)
            self._vim.call("ultest#adapter#run_test", test)

    def is_running(self, test_id: str) -> int:
        return int(test_id in self._processes)

    def clear(self):
        self._vim.log.debug("Clearing temp files")
        self._dir.cleanup()

    def create_attach_script(self, test_id: str) -> Optional[Tuple[str, str]]:
        """
        Create a python script to attach to a running tests process.

        This is a pretty simple hack where we create a script that will show
        the output of a test by tailing the test process's stdout which is
        written to a temp file, and sending all input to the process's stdin
        which is a FIFO/named pipe.
        """
        test_process = self._processes.get(test_id)
        if not test_process:
            return None
        from . import attach

        source = inspect.getsource(attach).format(**vars())
        script_path = os.path.join(self._dir.name, "attach.py")
        with open(script_path, "w") as script_file:
            script_file.write(source)
        return (test_process.out_path, script_path)
