import errno
import os
import pty
import select
from contextlib import contextmanager
from io import BufferedReader, BufferedWriter
from threading import Event, Thread
from typing import Iterator, Tuple, Union

from ...logging import get_logger


class ProcessIOHandle:
    """
    IO handle for a process which opens a named pipe for input to emulate an interactive session.
    """

    def __init__(self, in_path: str, out_path: str):
        self.in_path = in_path
        self.out_path = out_path
        self._close_event = Event()
        self._logger = get_logger()

    @contextmanager
    def open(
        self, use_pty: bool
    ) -> Iterator[Tuple[BufferedReader, Union[int, BufferedWriter]]]:
        """
        Open a reader, writer pair for processes to use for stdin & stdout/stderr

        To allow for other processes to send input without closing the pipe, a
        thread is spawned which holds it open until this function exits.
        """
        if use_pty:
            in_file = self._open_stdin()
            master_out_fd, slave_out_fd = pty.openpty()
            out_file = self._open_stdout()
            self._forward_output(master_out_fd, out_file)
        else:
            in_file = self._open_stdin()
            out_file = self._open_stdout()
        try:
            yield (in_file, slave_out_fd if use_pty else out_file)
        finally:
            out_file.close()

            self._close_event.set()
            in_file.close()
            if use_pty:
                os.close(master_out_fd)
            os.remove(self.in_path)

    def _open_stdin(self) -> BufferedReader:
        if os.path.exists(self.in_path):
            os.remove(self.in_path)
        os.mkfifo(self.in_path, 0o777)
        if self._close_event.is_set():
            raise IOError(f"Handle is already open for {self.in_path}")
        self._keep_stdin_open()
        return open(self.in_path, "rb")

    def _open_stdout(self) -> BufferedWriter:
        if os.path.exists(self.out_path):
            os.remove(self.out_path)
        return open(self.out_path, "wb")

    def _keep_stdin_open(self):
        def keep_open():
            with open(self.in_path, "wb"):
                self._close_event.wait()
                self._close_event.clear()

        Thread(target=keep_open).start()

    def _forward_output(self, out_fd: int, out_file: BufferedWriter):
        # Inspired by https://stackoverflow.com/questions/52954248/capture-output-as-a-tty-in-python
        def forward():
            while True:
                ready, _, _ = select.select([out_fd], [], [], 0.04)
                for fd in ready:
                    try:
                        data = os.read(fd, 512)
                        if not data:  # EOF
                            break
                        self._logger.debug(f"Writing data to output file")
                        out_file.write(data)
                    except OSError as e:
                        if e.errno != errno.EIO:
                            raise
                        # EIO means EOF on some systems
                        break
                out_file.flush()

        Thread(target=forward).start()
