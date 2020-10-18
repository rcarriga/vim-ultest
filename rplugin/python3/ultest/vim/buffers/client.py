from typing import List, Union
from ..base import BaseVimClient


class BufferClient:
    def __init__(self, vim: BaseVimClient):
        self._vim = vim

    def contents(self, buffer: Union[str, int], end_line: int = None) -> List[str]:
        return self._vim.sync_call("getbufline", buffer, 1, end_line or "$")

    def current_number(self):
        return self.number("%")

    def number(self, buffer: Union[int, str]):
        return self._vim.sync_call("bufnr", buffer)

    def clear_contents(self, buffer: Union[str, int]):
        self._vim.sync_call("deletebufline", buffer, 1, "$")

    def set_lines(
        self, buffer: Union[str, int], data: List[str], start: Union[int, str] = None
    ):
        if start is None:
            self.clear_contents(buffer)
            start = 1
        else:
            start = int(start)
        for line_no, line in enumerate(data):
            self._vim.sync_call("setbufline", buffer, start + line_no, line)

    def get_property(self, buffer: Union[str, int], prop: str) -> str:
        return self.get_var(buffer, f"&{prop}")

    def set_property(self, buffer: Union[str, int], prop: str, value):
        self.set_var(buffer, f"&{prop}", value)

    def get_var(self, buffer: Union[str, int], prop: str) -> str:
        return self._vim.sync_call("getbufvar", buffer, prop)

    def set_var(self, buffer: Union[str, int], prop: str, value):
        self._vim.sync_call("setbufvar", buffer, prop, value)

    def create(self, buf_name: str = "") -> int:
        return int(self._vim.sync_call("bufadd", buf_name))

    def current_line(self, buffer: Union[str, int] = None):
        if buffer:
            buf_info = self._vim.sync_eval(f"getbufinfo('{buffer}')[0]")
            line_num = buf_info.get("lnum")
        else:
            line_num = self._vim.sync_call("line", ".")
        return line_num
