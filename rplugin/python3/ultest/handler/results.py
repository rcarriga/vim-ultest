from typing import Dict, Iterable

from ultest.models import Position, Result, Test
from ultest.processors import Processors
from ultest.vim import VimClient


class Results:
    def __init__(self, vim: VimClient, processors: Processors):
        self._vim = vim
        self._results: Dict[str, Dict[str, Result]] = {}
        self._processors = processors

    def handle(self, result: Result):
        """
        Store a result and pass to processors.

        :param result: Result to store.
        :type result: Result
        """
        self._clear(result)
        if not self._results.get(result.file):
            self._results[result.file] = {}
        self._results[result.file][result.name] = result
        self._processors.exit(result, sync=False)

    def output(self, file_name: str, test_name: str, fail_only: bool = True) -> str:
        """
        Get the output of a result.

        :param file_name: Name of file to get output from.
        :type test_name: str
        :param test_name: Name of result to get.
        :type test_name: str
        :param fail_only: Only return output if result failed, defaults to True
        :type fail_only: bool, optional
        :return: Path to output file
        :rtype: str
        """
        result = self._results.get(file_name, {}).get(test_name)
        if result and (result.code or not fail_only):
            return result.output
        return ""

    def clear_old(self, file_name: str, positions: Iterable[Position]):
        """
        Clear results from storage that don't match the given positions.

        :param file_name: File to clear results from.
        :type file_name: str
        :param positions: Current positions for the named file.
        :type positions: Iterable[Position]
        """
        existing = set(position.name for position in positions)
        for name, res in self._results.get(file_name, {}).items():
            if name not in existing and res.file == file_name:
                self._clear(res)

    def _clear(self, test: Test):
        old_result = self._results.get(test.file, {}).pop(test.name, None)
        if old_result:
            self._processors.clear(old_result, sync=False)
