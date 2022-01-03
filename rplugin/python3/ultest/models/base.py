import json
from dataclasses import asdict, dataclass
from typing import List


@dataclass
class BasePosition:
    id: str
    name: str
    file: str
    line: int
    col: int
    running: int
    namespaces: List[str]
    type: str

    def __str__(self):
        props = self.dict()
        props["name"] = [ord(char) for char in self.name]
        return json.dumps(props)

    def dict(self):
        return asdict(self)
