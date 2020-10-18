import json
from dataclasses import dataclass, asdict


@dataclass
class BaseModel:
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return json.dumps(asdict(self))

    @property
    def dict(self):
        return asdict(self)
