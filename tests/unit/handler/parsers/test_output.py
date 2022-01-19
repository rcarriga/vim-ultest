from unittest import TestCase

from rplugin.python3.ultest.handler.parsers import OutputParser, ParseResult
from tests.mocks import get_output


class TestOutputParser(TestCase):
    def setUp(self) -> None:
        self.parser = OutputParser([])

    def test_parse_pytest(self):
        output = get_output("pytest")
        failed = list(self.parser.parse_failed("python#pytest", output))
        self.assertEqual(
            failed,
            [
                ParseResult(name="test_d", namespaces=["TestMyClass"]),
                ParseResult(name="test_parametrize", namespaces=[]),
                ParseResult(name="test_a", namespaces=[]),
            ],
        )

    def test_parse_pyunit(self):
        output = get_output("pyunit")
        failed = list(self.parser.parse_failed("python#pyunit", output))
        self.assertEqual(
            failed, [ParseResult(name="test_d", namespaces=["TestMyClass"])]
        )

    def test_parse_gotest(self):
        output = get_output("gotest")
        failed = list(self.parser.parse_failed("go#gotest", output))
        self.assertEqual(
            failed,
            [
                ParseResult(name="TestA", namespaces=[]),
                ParseResult(name="TestB", namespaces=[]),
            ],
        )

    def test_parse_jest(self):
        output = get_output("jest")
        failed = list(self.parser.parse_failed("javascript#jest", output))
        self.assertEqual(
            failed,
            [
                ParseResult(
                    name="it shouldn't pass",
                    namespaces=["First namespace", "Another namespace"],
                ),
                ParseResult(name="it shouldn't pass again", namespaces=[]),
            ],
        )

    def test_parse_exunit(self):
        output = get_output("exunit")
        failed = list(self.parser.parse_failed("elixir#exunit", output))
        self.assertEqual(
            failed,
            [
                ParseResult(name="the world", namespaces=[]),
                ParseResult(name="greets the world", namespaces=[]),
            ],
        )

    def test_parse_richgo(self):
        output = get_output("richgo")
        failed = list(self.parser.parse_failed("go#richgo", output))
        self.assertEqual(
            failed,
            [
                ParseResult(name="TestA", namespaces=[]),
                ParseResult(name="TestAAAB", namespaces=[]),
            ],
        )
    def test_parse_phpunit(self):
        output = get_output("phpunit")
        failed = list(self.parser.parse_failed("php#phpunit", output))
        self.assertEqual(
            failed,
            [
                ParseResult(name="test_fake", namespaces=["Tests\\FakeTest"])
            ]
        )
     
