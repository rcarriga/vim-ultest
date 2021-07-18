from dataclasses import dataclass, field
from typing import List

from .base import BasePosition
from .types import Literal


@dataclass
class File(BasePosition):
    running: int = 0
    line: Literal[0] = 0
    col: Literal[0] = 0
    namespaces: List[str] = field(default_factory=list)
    type: Literal["file"] = "file"
