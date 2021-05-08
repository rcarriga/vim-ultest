import random
from typing import List, Union

from hypothesis import given
from hypothesis.strategies import builds, integers, lists

from rplugin.python3.ultest.handler.parsers import Position
from rplugin.python3.ultest.models import File, Namespace, Test, Tree
from rplugin.python3.ultest.models.namespace import Namespace


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


@given(sorted_tests())
def test_get_nearest_from_strict_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    expected = tests[test_i]
    tree = Tree[Position].from_list([File(file="", name="", id=""), *tests])
    result = tree.sorted_search(expected.line, lambda test: test.line, strict=True)
    assert expected == result.data


@given(sorted_tests())
def test_get_nearest_from_strict_no_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    tree = Tree[Position].from_list([File(file="", name="", id=""), *tests])
    result = tree.sorted_search(
        tests[test_i].line + 1, lambda pos: pos.line, strict=True
    )
    assert result is None


@given(sorted_tests())
def test_get_nearest_from_non_strict_match(tests: List[Union[Test, Namespace]]):
    test_i = int(random.random() * len(tests))
    expected = tests[test_i]
    tree = Tree[Position].from_list([File(file="", name="", id=""), *tests])
    result = tree.sorted_search(expected.line + 1, lambda pos: pos.line, strict=False)
    assert expected == result.data


@given(sorted_tests(min_line=20))
def test_get_nearest_from_non_strict_no_match(tests: List[Union[Test, Namespace]]):
    line = 10
    tree = Tree[Position].from_list([File(file="", name="", id="", line=11), *tests])
    result = tree.sorted_search(line, lambda pos: pos.line, strict=False)
    assert result is None
