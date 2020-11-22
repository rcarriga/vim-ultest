import os
from typing import Dict, Iterable

from ..models import Position, Result, Test
from ..vim import VimClient


class Results:
    def __init__(self, vim: VimClient):
        self._vim = vim
        self._results: Dict[str, Dict[str, Result]] = {}

    def store(self, result: Result):
        self._clear(result)
        if not self._results.get(result.file):
            self._results[result.file] = {}
        self._results[result.file][result.name] = result

    def output(self, file_name: str, test_name: str, fail_only: bool = True) -> str:
        result = self._results.get(file_name, {}).get(test_name)
        if result and (result.code or not fail_only):
            return result.output
        return ""

    def clear_old(self, file_name: str, positions: Iterable[Position]):
        existing = set(position.name for position in positions)
        to_clear = [
            res
            for name, res in self._results.get(file_name, {}).items()
            if name not in existing and res.file == file_name
        ]
        for res in to_clear:
            self._clear(res)

    def _clear(self, test: Test):
        old_result = self._results.get(test.file, {}).pop(test.name, None)
        if old_result:
            self._vim.call("ultest#process#clear", old_result)
            if old_result.output:
                os.remove(old_result.output)
