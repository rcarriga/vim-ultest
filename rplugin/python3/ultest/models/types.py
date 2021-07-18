import sys
from typing import Any

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol
else:

    class _Literal:
        def __getitem__(self, a):
            return Any

    Literal = _Literal()

    class Protocol:
        ...
