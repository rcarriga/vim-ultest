import json
from dataclasses import asdict, dataclass, field
from typing import List


@dataclass(repr=False)
class File:

    id: str
    name: str
    file: str
    line: int = 0
    col: int = 0
    namespaces: List[str] = field(default_factory=list)
    type: str = "file"

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        props = self.dict()
        props["name"] = [int(char) for char in self.name.encode()]
        return json.dumps(props)

    def dict(self):
        return asdict(self)
