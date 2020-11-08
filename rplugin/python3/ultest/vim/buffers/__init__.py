from typing import List, Union
from ..base import BaseVimClient


class BufferClient:
    def __init__(self, vim: BaseVimClient):
        self._vim = vim

    def contents(self, buffer: Union[str, int], end_line: int = None) -> List[str]:
        return self._vim.sync_call("getbufline", buffer, 1, end_line or "$")

    def current_line(self, buffer: Union[str, int] = None):
        if buffer:
            buf_info = self._vim.sync_eval(f"getbufinfo('{buffer}')[0]")
            line_num = buf_info.get("lnum")
        else:
            line_num = self._vim.sync_call("line", ".")
        return line_num
