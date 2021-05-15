from typing import Union

from .file import File
from .namespace import Namespace
from .result import Result
from .test import Test
from .tree import Tree

Position = Union[Test, File, Namespace]
