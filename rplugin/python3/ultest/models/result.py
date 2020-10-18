from dataclasses import dataclass

from ultest.models.test import Test


@dataclass(repr=False)
class Result(Test):

    code: int
    output: str
