import json
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class Result:

    id: str
    file: str
    code: int
    output: str
    error_message: Optional[List[str]] = None
    error_line: Optional[int] = None

    def __str__(self):
        props = self.dict()
        return json.dumps(props)

    def dict(self):
        return {
            name: field for name, field in asdict(self).items() if field is not None
        }
