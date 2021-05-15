from dataclasses import dataclass
from typing import Literal

from .base import BasePosition


@dataclass
class Test(BasePosition):
    type: Literal["test"] = "test"
