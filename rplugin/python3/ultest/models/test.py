from dataclasses import dataclass

from .base import BasePosition
from .types import Literal


@dataclass
class Test(BasePosition):
    type: Literal["test"] = "test"
