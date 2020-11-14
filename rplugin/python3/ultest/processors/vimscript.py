from ultest.vim import VimClient
from ultest.processors.processor import Processor

PROCESSORS_VAR = "ultest#processors"
CONDITION = "condition"
START = "start"
CLEAR = "clear"
EXIT = "exit"


class VimscriptProcessor(Processor):
    def __init__(self, vim: VimClient):
        self._spec = {
            START: "ultest#process#start",
            CLEAR: "ultest#process#clear",
            EXIT: "ultest#process#exit",
        }
        super().__init__(vim)

    @property
    def condition(self):
        return True

    def clear(self, test, sync: bool = True):
        self._pass_to_processor(CLEAR, test, sync=sync)

    def start(self, test, sync: bool = True):
        self._pass_to_processor(START, test, sync=sync)

    def exit(self, test, sync: bool = True):
        self._pass_to_processor(EXIT, test, sync=sync)

    def _pass_to_processor(self, func: str, test, sync=True):
        caller = self._vim.sync_call if sync else self._vim.call
        if self._spec.get(func):
            caller(self._spec[func], test)  # type: ignore
