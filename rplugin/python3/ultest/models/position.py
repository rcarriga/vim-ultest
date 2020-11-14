import json
from dataclasses import dataclass, asdict


@dataclass(repr=False)
class Position:

    name: str
    file: str
    line: int
    col: int

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        props = self.dict
        props["name"] = [int(char) for char in self.name.encode()]
        return json.dumps(props)

    @property
    def dict(self):
        return asdict(self)
