import random
from rplugin.python3.ultest.models.namespace import Namespace
from typing import List, Union
from unittest.mock import Mock, mock_open, patch

import pytest
from hypothesis import given
from hypothesis.strategies import builds, integers, lists

from rplugin.python3.ultest.handler.finder import PositionFinder
from rplugin.python3.ultest.models import Test, Namespace
from tests.mocks import get_test_file


def sorted_tests(
    min_line: int = 1, max_line: int = 1000, min_length: int = 10, max_length: int = 20
):
    return lists(
        builds(
            Test,
            line=integers(min_value=min_line, max_value=max_line).map(
                lambda line: line * 2
            ),
        ),
        min_size=min_length,
        max_size=max_length,
        unique_by=lambda test: test.line,  # type: ignore
    ).map(lambda tests: sorted(tests, key=lambda test: test.line))


vim = Mock()
vim.launch = lambda f, _: f()
finder = PositionFinder(vim)


@given(sorted_tests())
def test_get_nearest_from_strict_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    expected = tests[test_i]
    result = finder.get_nearest_from(expected.line, tests, strict=True)
    assert expected == result


@given(sorted_tests())
def test_get_nearest_from_strict_no_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    result = finder.get_nearest_from(tests[test_i].line + 1, tests, strict=True)
    assert result is None


@given(sorted_tests())
def test_get_nearest_from_non_strict_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    expected = tests[test_i]
    result = finder.get_nearest_from(expected.line + 1, tests, strict=False)
    assert expected == result


@given(sorted_tests(min_line=20))
def test_get_nearest_from_non_strict_no_match(tests: List[Union[Test, Namespace]]):
    line = 10
    result = finder.get_nearest_from(line, tests, strict=False)
    assert result is None


@patch("builtins.open", mock_open(read_data=get_test_file("python")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_find_python_tests():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    tests = await finder.find_all("", patterns)

    expected = [
        Test(
            id=tests[0].id,
            name="test_a30",
            file="",
            line=3,
            col=1,
            running=0,
            namespaces=[],
        ),
        Namespace(
            id=tests[1].id,
            name="TestMock",
            file="",
            line=6,
            col=1,
            running=0,
            namespaces=[],
        ),
        Test(
            id=tests[2].id,
            name="test_a10",
            file="",
            line=7,
            col=1,
            running=0,
            namespaces=[tests[1].id],
        ),
        Test(
            id=tests[3].id,
            name="test_a43",
            file="",
            line=10,
            col=1,
            running=0,
            namespaces=[],
        ),
    ]

    assert tests == expected
