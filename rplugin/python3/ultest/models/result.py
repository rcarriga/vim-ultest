from dataclasses import dataclass

from .test import Test


@dataclass(repr=False)
class Result(Test):

    code: int
    output: str
