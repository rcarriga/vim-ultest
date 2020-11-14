from typing import List, Type

from ultest.processors.processor import Processor
from ultest.processors.vimscript import VimscriptProcessor
from ultest.models import Test, Result
from ultest.vim import VimClient

PROCESSORS_VAR = "ultest#processors"
PYTHON_PROCESSORS: List[Type[Processor]] = []


class Processors:
    def __init__(self, vim: VimClient):
        self._vim = vim
        vim_processor = VimscriptProcessor(vim)
        self._processors: List[Processor] = [vim_processor]

    def clear(self, test: Test, sync: bool = True):
        for processor in self._processors:
            processor.clear(test, sync)

    def start(self, test: Test, sync: bool = True):
        for processor in self._processors:
            processor.start(test, sync)

    def exit(self, result: Result, sync: bool = True):
        for processor in self._processors:
            processor.exit(result, sync)
