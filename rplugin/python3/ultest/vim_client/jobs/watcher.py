import itertools
import os
import threading
import warnings
from asyncio import events
from asyncio.log import logger
from asyncio.unix_events import AbstractChildWatcher


def _compute_returncode(status):
    if os.WIFSIGNALED(status):
        # The child process died because of a signal.
        return -os.WTERMSIG(status)
    elif os.WIFEXITED(status):
        # The child process exited (e.g sys.exit()).
        return os.WEXITSTATUS(status)
    else:
        # The child exited, but we don't understand its status.
        # This shouldn't happen, but if it does, let's just
        # return that status; perhaps that helps debug it.
        return status


# Ripped directly from https://github.com/python/cpython/blob/4649202ea75d48e1496e99911709824ca2d3170e/Lib/asyncio/unix_events.py#L1326


class ThreadedChildWatcher(AbstractChildWatcher):
    """Threaded child watcher implementation.
    The watcher uses a thread per process
    for waiting for the process finish.
    It doesn't require subscription on POSIX signal
    but a thread creation is not free.
    The watcher has O(1) complexity, its performance doesn't depend
    on amount of spawn processes.
    """

    def __init__(self):
        self._pid_counter = itertools.count(0)
        self._threads = {}

    def is_active(self):
        return True

    def close(self):
        self._join_threads()

    def _join_threads(self):
        """Internal: Join all non-daemon threads"""
        threads = [
            thread
            for thread in list(self._threads.values())
            if thread.is_alive() and not thread.daemon
        ]
        for thread in threads:
            thread.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __del__(self, _warn=warnings.warn):
        threads = [
            thread for thread in list(self._threads.values()) if thread.is_alive()
        ]
        if threads:
            _warn(
                f"{self.__class__} has registered but not finished child processes",
                ResourceWarning,
                source=self,
            )

    def add_child_handler(self, pid, callback, *args):
        loop = events.get_running_loop()
        thread = threading.Thread(
            target=self._do_waitpid,
            name=f"waitpid-{next(self._pid_counter)}",
            args=(loop, pid, callback, args),
            daemon=True,
        )
        self._threads[pid] = thread
        thread.start()

    def remove_child_handler(self, pid):
        # asyncio never calls remove_child_handler() !!!
        # The method is no-op but is implemented because
        # abstract base class requires it
        return True

    def attach_loop(self, loop):
        pass

    def _do_waitpid(self, loop, expected_pid, callback, args):
        assert expected_pid > 0

        try:
            pid, status = os.waitpid(expected_pid, 0)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen if waitpid() is called elsewhere).
            pid = expected_pid
            returncode = 255
            logger.warning(
                "Unknown child process pid %d, will report returncode 255", pid
            )
        else:
            returncode = _compute_returncode(status)
            if loop.get_debug():
                logger.debug(
                    "process %s exited with returncode %s", expected_pid, returncode
                )

        if loop.is_closed():
            logger.warning("Loop %r that handles pid %r is closed", loop, pid)
        else:
            loop.call_soon_threadsafe(callback, pid, returncode, *args)

        self._threads.pop(expected_pid)
