import re
from typing import Dict, List

from ultest.models import Test
from .base import BaseVimClient

REGEX_CONVERSIONS = {r"\\v": "", r"%\((.*?)\)": r"(?:\1)"}


class TestClient:
    """
    Helper functions to interact with vim-test
    """

    def __init__(self, vim: BaseVimClient):
        self._vim = vim
        self._patterns: Dict[str, Dict[str, List[str]]] = {}

    def run(self, test: Test):
        self._vim.call("ultest#adapter#run_test", str(test))

    def patterns(self, file_name: str):
        runner = self._vim.sync_call("test#determine_runner", file_name)
        if not runner:
            return {}
        file_type = runner.split("#")[0]
        known_patterns = self._patterns.get(file_type)
        if known_patterns:
            return known_patterns
        vim_patterns = self._get_vim_patterns(file_type)
        patterns = self._convert_patterns(vim_patterns)
        self._patterns[file_type] = patterns
        return patterns

    def _get_vim_patterns(self, file_type: str) -> Dict[str, List[str]]:
        try:
            vim_patterns = self._vim.sync_eval(f"g:test#{file_type}#patterns")
        except Exception:
            vim_patterns = {}
        return vim_patterns

    def _convert_patterns(self, vim_patterns: Dict[str, List[str]]):
        return {
            "test": [
                self._convert_regex(pattern) for pattern in vim_patterns.get("test", "")
            ],
            "namespace": [
                self._convert_regex(pattern)
                for pattern in vim_patterns.get("namespace", "")
            ],
        }

    def _convert_regex(self, vim_regex: str) -> str:
        regex = vim_regex.replace("\\" * 2, r"\\")
        for pattern, repl in REGEX_CONVERSIONS.items():
            regex = re.sub(pattern, repl, regex)
        return regex
