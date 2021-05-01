import inspect
import os
import re
import tempfile
from asyncio import CancelledError, subprocess
from contextlib import contextmanager
from io import BufferedReader, BufferedWriter
from os import path
from threading import Event, Thread
from typing import Dict, Iterator, List, Optional, Tuple

from ..logging import UltestLogger
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
        self._external_stdout: Dict[str, str] = {}

    def _safe_file_name(self, name: str) -> str:
        return re.subn(r"[.'\" \\/]", "_", name.replace(os.sep, "__"))[0]

    def _group_dir(self, file: str) -> str:
        return os.path.join(self._dir.name, self._safe_file_name(file))

    def _create_group_dir(self, file: str):
        path = self._group_dir(file)
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    async def run(
        self, cmd: List[str], group_id: str, process_id: str, cwd: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :param test: Test to build result from.
        :return: Exit code and path to file containing stdout/stderr
        """

        parent_dir = self._create_group_dir(group_id)
        stdin_path = path.join(parent_dir, f"{self._safe_file_name(process_id)}_in")
        stdout_path = path.join(parent_dir, f"{self._safe_file_name(process_id)}_out")
        test_process = TestProcess(
            in_path=stdin_path, out_path=stdout_path, logger=self._vim.log
        )
        self._processes[process_id] = test_process
        self._vim.log.fdebug("Starting test process {process_id} with command: {cmd}")
        try:
            async with self._vim.semaphore:
                with test_process.open() as (in_handle, out_handle):
                    try:
                        process = await subprocess.create_subprocess_exec(
                            *cmd,
                            stdin=in_handle,
                            stderr=out_handle,
                            stdout=out_handle,
                            cwd=cwd,
                        )
                    except CancelledError:
                        raise
                    except Exception:
                        self._vim.log.warn(
                            f"An exception was thrown when starting process {process_id} with command: {cmd}",
                            exc_info=True,
                        )
                        code = 1
                    else:
                        test_process.process = process
                        code = await process.wait()
                    self._vim.log.fdebug(
                        "Process {process_id} complete with exit code: {code}"
                    )
                    return (code, stdout_path)
        finally:
            del self._processes[process_id]

    def register_new_process(self, process_id: str):
        self._processes[process_id] = None

    def register_external_output(self, process_id: str, path: str):
        self._vim.log.finfo(
            "Saving external stdout path '{path}' for test {process_id}"
        )
        self._external_stdout[process_id] = path

    def clear_external_output(self, process_id: str):
        self._vim.log.finfo("Removing external stdout path for test {process_id}")
        self._external_stdout.pop(process_id, None)

    def is_running(self, process_id: str) -> int:
        return int(process_id in self._processes)

    def clear(self):
        self._vim.log.debug("Clearing temp files")
        self._dir.cleanup()

    def create_attach_script(self, process_id: str) -> Optional[Tuple[str, str]]:
        """
        Create a python script to attach to a running tests process.

        This is a pretty simple hack where we create a script that will show
        the output of a test by tailing the test process's stdout which is
        written to a temp file, and sending all input to the process's stdin
        which is a FIFO/named pipe.
        """
        test_process = self._processes.get(process_id)
        if test_process:
            OUT_FILE = test_process.out_path
            IN_FILE = test_process.in_path
        else:
            OUT_FILE = self._external_stdout.get(process_id)
            IN_FILE = None

        if not OUT_FILE:
            return None

        from . import attach

        source = inspect.getsource(attach).format(IN_FILE=IN_FILE, OUT_FILE=OUT_FILE)
        script_path = os.path.join(self._dir.name, "attach.py")
        with open(script_path, "w") as script_file:
            script_file.write(source)
        return (OUT_FILE, script_path)
