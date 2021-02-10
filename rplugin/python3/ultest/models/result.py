import json
from dataclasses import asdict, dataclass


@dataclass(repr=False)
class Result:

    id: str
    file: str
    code: int
    output: str

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        props = self.dict
        return json.dumps(props)

    @property
    def dict(self):
        return asdict(self)
