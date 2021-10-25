from typing import Any, Callable, Coroutine, List

from pynvim import Nvim

from .jobs import JobManager


class VimClient:
    def __init__(self, vim_: Nvim):
        self._vim = vim_
        num_threads = int(self.sync_eval("g:ultest_max_threads"))  # type: ignore
        self._job_manager = JobManager(num_threads)

    @property
    def semaphore(self):
        return self._job_manager.semaphore

    def message(self, message, sync=False):
        if not isinstance(message, str) or not message.endswith("\n"):
            message = str(message) + "\n"
        if sync:
            self._vim.out_write(message)
        else:
            self.schedule(self._vim.out_write, message)

    def schedule(self, func: Callable, *args, **kwargs) -> None:
        """
        Schedule a function to be called on Vim thread.

        :param func: Function to run.
        :param *args: Positional args for function.
        :param **kwargs: Keywords args for function.
        """
        self._vim.async_call(func, *args, **kwargs)

    def launch(
        self,
        func: Coroutine,
        job_group: str,
    ) -> None:
        """
        Launch a function to be run on a separate thread.

        :param func: Function to run.
        :param *args: Positional args for function.
        :param **kwargs: kwargs for function.
        """
        self._job_manager.run(func, job_group=job_group)

    def stop(self, job_group: str) -> bool:
        """
        Stop all jobs associated with the given job group

        :param job_group:  group for a group of jobs
        """
        return self._job_manager.stop_jobs(job_group)

    def command(
        self,
        command: str,
        *args,
        **kwargs,
    ):
        """
        Call a Vim command asynchronously. This can be called from a thread to be
        scheduled on the main Vim thread.
        Args are supplied first. Kwargs are supplied after in the format "name=value"

        :param command: Command to run
        :param callback: Function to supply resulting output to.
        """

        def runner():
            expr = self.construct_command(command, *args, **kwargs)
            self._vim.command(expr, async_=True)

        self.schedule(runner)

    def sync_command(self, command: str, *args, **kwargs) -> List[str]:
        """
        Call a Vim command.
        Args are supplied first. Kwargs are supplied after in the format "name=value"

        :param command: Command to run
        """
        expr = self.construct_command(command, *args, **kwargs)
        output = self._vim.command_output(expr)
        return output.splitlines() if output else []  # type: ignore

    def construct_command(self, command, *args, **kwargs):
        args_str = " ".join(f"{arg}" for arg in args)
        kwargs_str = " ".join(f" {name}={val}" for name, val in kwargs.items())
        return f"{command} {args_str} {kwargs_str}"

    def call(self, func: str, *args) -> None:
        """
        Call a vimscript function asynchronously. This can be called
        from a different thread to main Vim thread.

        :param func: Name of function to call.
        :param args: Arguments for the function.
        :rtype: None
        """
        expr = self.construct_function(func, *args)

        def runner():
            self._eval(expr, sync=False)

        self.schedule(runner)

    def sync_call(self, func: str, *args) -> Any:
        """
        Call a vimscript function from the main Vim thread.

        :param func: Name of function to call.
        :param args: Arguments for the function.
        :return: Result of function call.
        :rtype: Any
        """
        expr = self.construct_function(func, *args)
        return self._eval(expr, sync=True)

    def eval(self, expr: str) -> Any:
        return self._eval(expr, sync=False)

    def sync_eval(self, expr: str) -> Any:
        return self._eval(expr, sync=True)

    def construct_function(self, func: str, *args):
        func_args = ", ".join(self._convert_arg(arg) for arg in args)
        return f"{func}({func_args})"

    def _eval(self, expr: str, sync: bool):
        return self._vim.eval(expr, async_=not sync)

    def _convert_arg(self, arg):
        if isinstance(arg, str) and self._needs_quotes(arg):
            return f"'{arg}'"
        if isinstance(arg, bool):
            arg = 1 if arg else 0
        if isinstance(arg, list):
            return f"[{','.join(self._convert_arg(elem) for elem in arg)}]"
        if isinstance(arg, tuple):
            return self._convert_arg(list(arg))
        return str(arg)

    def _needs_quotes(self, arg: str) -> bool:
        if not any(char in arg for char in "\"'("):
            return not (len(arg) == 2 and arg[1] == ":")
        return False
