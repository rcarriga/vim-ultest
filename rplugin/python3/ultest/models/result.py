import json
from dataclasses import asdict, dataclass


@dataclass
class Result:

    id: str
    file: str
    code: int
    output: str

    def __str__(self):
        props = self.dict()
        return json.dumps(props)

    def dict(self):
        return asdict(self)
