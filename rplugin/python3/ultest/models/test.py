from dataclasses import dataclass
from .position import Position


@dataclass(repr=False)
class Test(Position):

    id: str
