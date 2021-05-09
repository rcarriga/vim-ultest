from dataclasses import dataclass, field
from typing import List, Literal

from .base import BasePosition


@dataclass
class File(BasePosition):
    running: int = 0
    line: Literal[0] = 0
    col: Literal[0] = 0
    namespaces: List[str] = field(default_factory=list)
    type: Literal["file"] = "file"
