import json
from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class Test:

    id: str
    name: str
    file: str
    line: int
    col: int
    running: int
    namespaces: List[str] = field(default_factory=list)
    type: str = "test"

    def __str__(self):
        props = self.dict()
        props["name"] = [int(char) for char in self.name.encode()]
        return json.dumps(props)

    def dict(self):
        return asdict(self)
