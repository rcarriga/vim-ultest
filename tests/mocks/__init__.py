import os
from typing import List


def get_output(runner: str) -> List[str]:
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "test_outputs", runner)
    with open(filename) as output:
        return output.readlines()


def get_test_file(name: str) -> str:
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "test_files", name)
    with open(filename) as output:
        return output.read()
