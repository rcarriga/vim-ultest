from dataclasses import dataclass

from .base import BasePosition
from .types import Literal


@dataclass
class Namespace(BasePosition):
    type: Literal["namespace"] = "namespace"
