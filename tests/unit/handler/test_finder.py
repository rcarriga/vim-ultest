import random
from typing import List
from unittest.mock import Mock, mock_open, patch

from asynctest import TestCase
from hypothesis import given
from hypothesis.strategies import builds, integers, lists

from rplugin.python3.ultest.handler.finder import TestFinder
from rplugin.python3.ultest.models.test import Test
from tests.mocks.test_files import mock_python_file


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


class TestTestFinder(TestCase):
    def setUp(self) -> None:
        self.vim = Mock()
        self.vim.launch = lambda f, _: f()
        self.finder = TestFinder(self.vim)

    @given(sorted_tests())
    def test_get_nearest_from_strict_match(self, tests: List[Test]):
        test_i = int(random.random() * len(tests))
        expected = tests[test_i]
        result = self.finder.get_nearest_from(expected.line, tests, strict=True)
        self.assertEqual(expected, result)

    @given(sorted_tests())
    def test_get_nearest_from_strict_no_match(self, tests: List[Test]):
        test_i = int(random.random() * len(tests))
        result = self.finder.get_nearest_from(
            tests[test_i].line + 1, tests, strict=True
        )
        self.assertIsNone(result)

    @given(sorted_tests())
    def test_get_nearest_from_non_strict_match(self, tests: List[Test]):
        test_i = int(random.random() * len(tests))
        expected = tests[test_i]
        result = self.finder.get_nearest_from(expected.line + 1, tests, strict=False)
        self.assertEqual(expected, result)

    @given(sorted_tests(min_line=20))
    def test_get_nearest_from_non_strict_no_match(self, tests: List[Test]):
        line = 10
        result = self.finder.get_nearest_from(line, tests, strict=False)
        self.assertIsNone(result)

    @patch("builtins.open", mock_open(read_data=mock_python_file))
    @patch("builtins.hash", lambda o: len(".".join(o)))
    @patch("os.path.isfile", lambda _: True)
    async def test_find_python_tests(self):
        patterns = {
            "test": [r"\v^\s*%(async )?def (test_\w+)"],
            "namespace": [r"\v^\s*class (\w+)"],
        }

        expected = [
            Test(
                id="test_a3025",
                name="test_a30",
                file="",
                line=4,
                col=1,
                running=0,
            ),
            Test(
                id="test_a4341",
                name="test_a43",
                file="",
                line=7,
                col=1,
                running=0,
            ),
        ]

        results = await self.finder.find_all("", patterns)

        self.assertEqual(results, expected)
