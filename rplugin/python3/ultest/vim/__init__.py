from typing import Any, Callable, Optional, List

from pynvim import Nvim
from .threader import Threader


class VimClient:
    def __init__(self, vim: Nvim):
        self._vim = vim
        num_threads = int(self._vim.eval("g:ultest_max_threads"))
        self._threader = Threader(num_threads)

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
        :type func: Callable
        :param *args: Positional args for function.
        :param **kwargs: Keywords args for function.
        """
        self._vim.async_call(func, *args, **kwargs)

    def launch(self, func: Callable, *args, **kwargs) -> None:
        """
        Launch a function to be run on a separate thread.

        :param func: Function to run.
        :type func: Callable
        :param *args: Positional args for function.
        :param **kwargs: Keywords args for function.
        """
        runner = lambda: func(*args, **kwargs)
        self._threader.run(runner)()

    def command(
        self,
        command: str,
        *args,
        callback: Optional[Callable[[List[str]], None]] = None,
        **kwargs,
    ):
        """
        Call a Vim command asynchronously. This can be called from a thread to be
        scheduled on the main Vim thread.
        Args are supplied first. Kwargs are supplied after in the format "name=value"

        :param command: Command to run
        :type command: str
        :param callback: Function to supply resulting output to.
        :type callback: Optional[Callable]
        """
        runner = (
            lambda: callback(self.sync_command(command, *args, **kwargs))
            if callback
            else self.sync_command(command, *args, **kwargs)
        )
        self.schedule(runner)

    def sync_command(self, command: str, *args, **kwargs) -> List[str]:
        """
        Call a Vim command.
        Args are supplied first. Kwargs are supplied after in the format "name=value"

        :param command: Command to run
        :type command: str
        """
        expr = self.construct_command(command, *args, **kwargs)
        output = self._vim.command_output(expr)
        return output.splitlines() if output else []

    def construct_command(self, command, *args, **kwargs):
        args_str = " ".join(f"{arg}" for arg in args)
        kwargs_str = " ".join(f" {name}={val}" for name, val in kwargs.items())
        return f"{command} {args_str} {kwargs_str}"

    def call(self, func: str, *args, callback: Optional[Callable] = None) -> None:
        """
        Call a vimscript function asynchronously. This can be called
        from a different thread to main Vim thread.

        :param func: Name of function to call.
        :type func: str
        :param args: Arguments for the function.
        :param callback: Callback to send result of function to, defaults to None
        :type callback: Optional[Callable]
        :rtype: None
        """
        runner = (
            lambda: callback(self.sync_call(func, *args))
            if callback
            else self.sync_call(func, *args)
        )
        self.schedule(runner)

    def sync_call(self, func: str, *args) -> Any:
        """
        Call a vimscript function from the main Vim thread.

        :param func: Name of function to call.
        :type func: str
        :param args: Arguments for the function.
        :return: Result of function call.
        :rtype: Any
        """
        expr = self.construct_function(func, *args)
        return self._eval(expr)

    def sync_eval(self, expr: str) -> Any:
        return self._vim.eval(expr)

    def construct_function(self, func: str, *args):
        func_args = ", ".join(self._convert_arg(arg) for arg in args)
        return f"{func}({func_args})"

    def _eval(self, expr: str):
        return self._vim.eval(expr)

    def _convert_arg(self, arg):
        if isinstance(arg, str) and self._needs_quotes(arg):
            return f"'{arg}'"
        if isinstance(arg, bool):
            arg = 1 if arg else 0
        return str(arg)

    def _needs_quotes(self, arg: str) -> bool:
        if not any(char in arg for char in "\"'("):
            return not (len(arg) == 2 and arg[1] == ":")
        return False
