import os
from typing import Dict, Iterable, Optional

from ..models import Result, Test


class ResultStore:
    def __init__(self):
        self._results: Dict[str, Dict[str, Result]] = {}

    def add(self, file_name: str, result: Result):
        if not self._results.get(file_name):
            self._results[file_name] = {}
        self._results[file_name][result.id] = result

    def get(self, file_name: str, test_id: str) -> Optional[Result]:
        return self._results.get(file_name, {}).pop(test_id, None)

    def pop(self, file_name: str, test_id: str) -> Optional[Result]:
        return self._results.get(file_name, {}).pop(test_id, None)
