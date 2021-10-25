from unittest import TestCase

from rplugin.python3.ultest.handler.parsers import OutputParser, ParseResult
from tests.mocks import get_output


class TestOutputParser(TestCase):
    def setUp(self) -> None:
        self.parser = OutputParser([])

    def test_parse_gotest(self):
        output = get_output("gotest")
        failed = list(self.parser.parse_failed("go#gotest", output))
        self.assertEqual(
            failed,
            [
                ParseResult(file="", name="TestA", namespaces=[]),
                ParseResult(file="", name="TestB", namespaces=[]),
            ],
        )

    def test_parse_jest(self):
        output = get_output("jest")
        failed = list(self.parser.parse_failed("javascript#jest", output))
        self.assertEqual(
            failed,
            [
                ParseResult(
                    file="",
                    name="it shouldn't pass",
                    namespaces=["First namespace", "Another namespace"],
                ),
                ParseResult(file="", name="it shouldn't pass again", namespaces=[]),
            ],
        )

    def test_parse_exunit(self):
        output = get_output("exunit")
        failed = list(self.parser.parse_failed("elixir#exunit", output))
        self.assertEqual(
            failed,
            [
                ParseResult(file="", name="the world", namespaces=[]),
                ParseResult(file="", name="greets the world", namespaces=[]),
            ],
        )

    def test_parse_richgo(self):
        output = get_output("richgo")
        failed = list(self.parser.parse_failed("go#richgo", output))
        self.assertEqual(
            failed,
            [
                ParseResult(file="", name="TestA", namespaces=[]),
                ParseResult(file="", name="TestAAAB", namespaces=[]),
            ],
        )
