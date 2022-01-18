from unittest import TestCase

from rplugin.python3.ultest.handler.parsers.output import OutputParser
from rplugin.python3.ultest.handler.parsers.output.python.unittest import (
    ErroredTestError,
    ParseResult,
    failed_test,
)
from tests.mocks import get_output


class TestUnittestParser(TestCase):
    def test_parse_failed_test(self):
        raw = """======================================================================
FAIL: test_b (test_a.TestClass)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/ronan/tests/test_a.py", line 34, in test_b
    self.assertEqual({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 5, "c": 3, "d": 4})
AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}
- {'a': 1, 'b': 2, 'c': 3}
?               ^

+ {'a': 1, 'b': 5, 'c': 3, 'd': 4}
?               ^        ++++++++

"""

        expected = ParseResult(
            name="test_b",
            namespaces=["TestClass"],
            file="/home/ronan/tests/test_a.py",
            line=34,
            message=[
                "AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                "- {'a': 1, 'b': 2, 'c': 3}",
                "?               ^",
                "",
                "+ {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                "?               ^        ++++++++",
            ],
        )
        result = failed_test.parse(raw)
        self.assertEqual(result, expected)

    def test_parse_errored_test_raises(self):
        raw = """======================================================================
ERROR: test_c (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_c
Traceback (most recent call last):
  File "/home/ronan/.pyenv/versions/3.8.6/lib/python3.8/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/home/ronan/.pyenv/versions/3.8.6/lib/python3.8/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/ronan/tests/test_c.py", line 6, in <module>
    class CTests(TestCase):
  File "/home/ronan/tests/test_c.py", line 8, in CTests
    @not_a_decorator
NameError: name 'not_a_decorator' is not defined

"""
        with self.assertRaises(ErroredTestError):
            failed_test.parse(raw)

    def test_parse_unittest(self):
        parser = OutputParser([])
        raw = get_output("pyunit")
        result = parser.parse_failed("python#pyunit", raw)
        expected = [
            ParseResult(
                name="test_c",
                namespaces=["TestClass"],
                file="/home/ronan/tests/test_a.py",
                message=["Exception"],
                output=None,
                line=37,
            ),
            ParseResult(
                name="test_b",
                namespaces=["TestClass"],
                file="/home/ronan/tests/test_a.py",
                message=[
                    "AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                    "- {'a': 1, 'b': 2, 'c': 3}",
                    "?               ^",
                    "",
                    "+ {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                    "?               ^        ++++++++",
                ],
                output=None,
                line=34,
            ),
            ParseResult(
                name="test_a",
                namespaces=["AnotherClass"],
                file="/home/ronan/tests/test_b.py",
                message=["AssertionError"],
                output=None,
                line=7,
            ),
            ParseResult(
                name="test_thing",
                namespaces=["TestStuff"],
                file="/home/ronan/tests/tests/test_c.py",
                message=["AssertionError"],
                output=None,
                line=6,
            ),
        ]
        self.assertEqual(expected, result)
