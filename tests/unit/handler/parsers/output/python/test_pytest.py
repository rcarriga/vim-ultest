from dataclasses import asdict
from unittest import TestCase

from rplugin.python3.ultest.handler.parsers.output import OutputParser
from rplugin.python3.ultest.handler.parsers.output.python.pytest import (
    ParseResult,
    failed_test_section,
    failed_test_section_code,
    failed_test_section_error_message,
    failed_test_section_title,
)
from tests.mocks import get_output


class TestPytestParser(TestCase):
    def test_parse_file(self):
        output = get_output("pytest")
        parser = OutputParser([])
        result = parser.parse_failed("python#pytest", output)
        self.assertEqual(
            result,
            [
                ParseResult(
                    name="test_b",
                    namespaces=[],
                    file="test_a.py",
                    message=["Exception: OH NO"],
                    output=None,
                    line=21,
                ),
                ParseResult(
                    name="test_b",
                    namespaces=["TestClass"],
                    file="test_a.py",
                    message=[
                        "AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                        "- {'a': 1, 'b': 2, 'c': 3}",
                        "?               ^",
                        "",
                        "+ {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
                        "?               ^        ++++++++",
                    ],
                    output=None,
                    line=29,
                ),
                ParseResult(
                    name="test_c",
                    namespaces=["TestClass"],
                    file="test_a.py",
                    message=["Exception"],
                    output=None,
                    line=39,
                ),
                ParseResult(
                    name="test_a",
                    namespaces=[],
                    file="test_b.py",
                    message=["assert 2 == 3"],
                    output=None,
                    line=5,
                ),
                ParseResult(
                    name="test_d",
                    namespaces=[],
                    file="test_b.py",
                    message=["assert 2 == 3"],
                    output=None,
                    line=16,
                ),
                ParseResult(
                    name="test_a",
                    namespaces=[],
                    file="test_x.py",
                    message=["assert False"],
                    output=None,
                    line=6,
                ),
                ParseResult(
                    name="test_a30",
                    namespaces=[],
                    file="tests/test_c.py",
                    message=["assert 2 == 3"],
                    output=None,
                    line=23,
                ),
            ],
        )

    def test_parse_failed_test_section_title(self):
        raw = "_____ MyClass.test_a ______"
        result = failed_test_section_title.parse(raw)
        self.assertEqual(result, (["MyClass"], "test_a"))

    def test_parse_failed_test_section_error(self):
        self.maxDiff = None
        raw = """E       AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}
E       - {'a': 1, 'b': 2, 'c': 3}
E       ?               ^
E       
E       + {'a': 1, 'b': 5, 'c': 3, 'd': 4}
E       ?               ^        ++++++++
"""
        result = failed_test_section_error_message.parse(raw)
        expected = [
            "AssertionError: {'a': 1, 'b': 2, 'c': 3} != {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
            "- {'a': 1, 'b': 2, 'c': 3}",
            "?               ^",
            "",
            "+ {'a': 1, 'b': 5, 'c': 3, 'd': 4}",
            "?               ^        ++++++++",
        ]
        self.assertEqual(expected, result)

    def test_parse_failed_test_section_code(self):
        self.maxDiff = None
        raw = """self = <test_a.TestClass testMethod=test_b>

    def test_b(self):
>       self.assertEqual({
            "a": 1,
         "b": 2,
         "c": 3},
         {"a": 1,
         "b": 5,
         "c": 3,
         "d": 4})
E This should not be parsed"""
        result, _ = failed_test_section_code.parse_partial(raw)
        expected = [
            "self = <test_a.TestClass testMethod=test_b>",
            "",
            "    def test_b(self):",
            ">       self.assertEqual({",
            '            "a": 1,',
            '         "b": 2,',
            '         "c": 3},',
            '         {"a": 1,',
            '         "b": 5,',
            '         "c": 3,',
            '         "d": 4})',
        ]
        self.assertEqual(expected, result)

    def test_parse_failed_test_section(self):
        raw = """_____________________________________________________________________ MyClass.test_b _____________________________________________________________________

self = <test_a.MyClass testMethod=test_b>

    def test_b(self):
        \"""
        tests
    
        :param: b teststst
        \"""
        a = [[3, 1, 2, 3], 2, 4, 5]
        breakpoint()
>       a[0] = 3
E       Exception: OH NO

test_a.py:20: Exception
-------------------------------------------------------------- Captured stdout call --------------------------------------------------------------
[3, 2, 4, 5]
[3, 2, 4, 5]
"""
        result = failed_test_section.parse(raw)
        self.assertEqual(
            result,
            ParseResult(
                file="test_a.py",
                name="test_b",
                namespaces=["MyClass"],
                message=["Exception: OH NO"],
                line=20,
            ),
        )

    def test_parse_failed_test_section_with_trace(self):
        raw = """_______________________________ TestClass.test_c _______________________________

self = <test_a.TestClass testMethod=test_c>

    def test_c(self):
>       a_function()

test_a.py:39: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def a_function():
        x = 3
        print(x)
>       raise Exception("OH NO")
E       Exception: OH NO

tests/__init__.py:6: Exception OH NO
----------------------------- Captured stdout call -----------------------------
3
"""
        result = failed_test_section.parse(raw)
        self.assertEqual(
            asdict(result),
            asdict(
                ParseResult(
                    file="test_a.py",
                    name="test_c",
                    namespaces=["TestClass"],
                    message=["Exception: OH NO"],
                    line=39,
                )
            ),
        )
