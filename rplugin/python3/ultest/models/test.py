from dataclasses import dataclass
from ultest.models.position import Position


@dataclass(repr=False)
class Test(Position):

    id: int
