import inspect
import os
import re
import tempfile
from asyncio import CancelledError, subprocess
from os import path
from typing import Dict, List, Optional, Tuple

from ...vim_client import VimClient
from .handle import ProcessIOHandle


class ProcessManager:
    """
    Handle scheduling and running tests.
    """

    def __init__(self, vim: VimClient):
        self._vim = vim
        self._dir = tempfile.TemporaryDirectory(prefix="ultest")
        self._processes: Dict[str, Optional[ProcessIOHandle]] = {}
        self._external_stdout: Dict[str, str] = {}

    async def run(
        self,
        cmd: List[str],
        group_id: str,
        process_id: str,
        cwd: Optional[str] = None,
        env: Optional[Dict] = None,
    ) -> Tuple[int, str]:
        """
        Run a test with the given command.

        Constucts a result from the given test.

        :param cmd: Command arguments to run
        :return: Exit code and path to file containing stdout/stderr
        """

        parent_dir = self._create_group_dir(group_id)
        stdin_path = path.join(parent_dir, f"{self._safe_file_name(process_id)}_in")
        stdout_path = path.join(parent_dir, f"{self._safe_file_name(process_id)}_out")
        io_handle = ProcessIOHandle(in_path=stdin_path, out_path=stdout_path)
        self._processes[process_id] = io_handle
        self._vim.log.fdebug(
            "Starting test process {process_id} with command {cmd}, cwd = {cwd}, env = {env}"
        )
        try:
            async with self._vim.semaphore:
                with io_handle.open() as (in_handle, out_handle):
                    try:
                        process = await subprocess.create_subprocess_exec(
                            *cmd,
                            stdin=in_handle,
                            stderr=out_handle,
                            stdout=out_handle,
                            cwd=cwd,
                            env=env and {**os.environ, **env},
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
                        code = await process.wait()
                    self._vim.log.fdebug(
                        "Process {process_id} complete with exit code: {code}"
                    )
                    return (code, stdout_path)
        finally:
            del self._processes[process_id]

    def _safe_file_name(self, name: str) -> str:
        return re.subn(r"[.'\" \\/]", "_", name.replace(os.sep, "__"))[0]

    def _group_dir(self, file: str) -> str:
        return os.path.join(self._dir.name, self._safe_file_name(file))

    def _create_group_dir(self, file: str):
        path = self._group_dir(file)
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

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
