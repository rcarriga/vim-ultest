from dataclasses import dataclass
from typing import Literal

from .base import BasePosition


@dataclass
class Namespace(BasePosition):
    type: Literal["namespace"] = "namespace"
