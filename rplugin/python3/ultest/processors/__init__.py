from typing import List, Callable, Any, Type

from ultest.processors.processor import Processor
from ultest.processors.vimscript import VimscriptProcessor
from ultest.models import Test, Result
from ultest.vim import VimClient

PROCESSORS_VAR = "ultest#processors"
PYTHON_PROCESSORS: List[Type[Processor]] = []


class Processors:
    def __init__(self, vim: VimClient):
        self._vim = vim
        vim_processors: List[Processor] = [
            VimscriptProcessor(spec, vim)
            for spec in self._vim.sync_call("nvim_get_var", PROCESSORS_VAR) or []
        ]
        python_processors = [
            constructor(vim) for constructor in PYTHON_PROCESSORS
        ]  # pylint: disable=E1120
        self._processors: List[Processor] = [
            processor
            for processor in (vim_processors + python_processors)
            if processor.condition
        ]

    def clear(self, test: Test, sync: bool = True):
        for processor in self._processors:
            processor.clear(test, sync)

    def start(self, test: Test, sync: bool = True):
        for processor in self._processors:
            processor.start(test, sync)

    def exit(self, result: Result, sync: bool = True):
        for processor in self._processors:
            processor.exit(result, sync)
