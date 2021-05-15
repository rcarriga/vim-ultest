import sys

sys.path
sys.path.append("rplugin/python3/")

import ultest  # type: ignore

sys.modules["rplugin.python3.ultest"] = ultest

import hypothesis
from hypothesis import settings

settings.register_profile(
    "default", max_examples=1, suppress_health_check=[hypothesis.HealthCheck.too_slow]
)

settings.load_profile("default")
