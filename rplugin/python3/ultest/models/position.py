from dataclasses import dataclass
from ultest.models.base import BaseModel


@dataclass(repr=False)
class Position(BaseModel):

    name: str
    file: str
    line: int
    col: int
