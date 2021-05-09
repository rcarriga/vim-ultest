import os
from contextlib import contextmanager
from io import BufferedReader, BufferedWriter
from threading import Event, Thread
from typing import Iterator, Tuple


class ProcessIOHandle:
    """
    IO handle for a process which opens a named pipe for input to emulate an interactive session.
    """

    def __init__(self, in_path: str, out_path: str):
        self.in_path = in_path
        self.out_path = out_path
        self._close_event = Event()

    @contextmanager
    def open(self) -> Iterator[Tuple[BufferedReader, BufferedWriter]]:
        """
        Open a reader, writer pair for processes to use for stdin & stdout/stderr

        To allow for other processes to send input without closing the pipe, a
        thread is spawned which holds it open until this function exits.
        """
        in_handle = self._open_stdin()
        out_handle = self._open_stdout()
        try:
            yield (in_handle, out_handle)
        finally:
            out_handle.close()

            self._close_event.set()
            in_handle.close()
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
