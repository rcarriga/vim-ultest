from unittest.mock import Mock, mock_open, patch

import pytest

from rplugin.python3.ultest.handler.parsers import FileParser
from rplugin.python3.ultest.models import Namespace, Test
from rplugin.python3.ultest.models.file import File
from rplugin.python3.ultest.models.namespace import Namespace
from tests.mocks import get_test_file

vim = Mock()
vim.launch = lambda f, _: f()
file_parser = FileParser(vim)


@patch("builtins.open", mock_open(read_data=get_test_file("python")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_python_tests():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    tests = list(await file_parser.parse_file_structure("", patterns))

    expected = [
        File(id="", name="", file="", line=0, col=0, namespaces=[], type="file"),
        Test(
            id=tests[1].id,
            name="test_a",
            file="",
            line=4,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
        Namespace(
            id=tests[2].id,
            name="TestAgain",
            file="",
            line=9,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Test(
            id=tests[3].id,
            name="test_d",
            file="",
            line=10,
            col=1,
            running=0,
            namespaces=[tests[2].id],
            type="test",
        ),
        Test(
            id=tests[4].id,
            name="test_a",
            file="",
            line=16,
            col=1,
            running=0,
            namespaces=[tests[2].id],
            type="test",
        ),
        Namespace(
            id=tests[5].id,
            name="TestMyClass",
            file="",
            line=25,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Test(
            id=tests[6].id,
            name="test_d",
            file="",
            line=26,
            col=1,
            running=0,
            namespaces=[tests[5].id],
            type="test",
        ),
        Test(
            id=tests[7].id,
            name="test_a",
            file="",
            line=29,
            col=1,
            running=0,
            namespaces=[tests[5].id],
            type="test",
        ),
        Test(
            id=tests[8].id,
            name="test_b",
            file="",
            line=33,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
    ]

    assert tests == expected


@patch("builtins.open", mock_open(read_data=get_test_file("jest")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_jest_tests():
    patterns = {
        "test": [r'\v^\s*%(it|test)\s*[( ]\s*%("|' '|`)(.*)%("|' "|`)"],
        "namespace": [
            r'\v^\s*%(describe|suite|context)\s*[( ]\s*%("|' '|`)(.*)%("|' "|`)"
        ],
    }

    tests = list(await file_parser.parse_file_structure("", patterns))

    expected = [
        File(
            id="",
            name="",
            file="",
            line=0,
            col=0,
            running=0,
            namespaces=[],
            type="file",
        ),
        Namespace(
            id=tests[1].id,
            name='First namespace", () => {',
            file="",
            line=1,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Namespace(
            id=tests[2].id,
            name='Second namespace", () => {',
            file="",
            line=2,
            col=1,
            running=0,
            namespaces=[tests[1].id],
            type="namespace",
        ),
        Test(
            id=tests[3].id,
            name="it shouldn't pass\", () => {",
            file="",
            line=3,
            col=1,
            running=0,
            namespaces=[
                tests[1].id,
                tests[2].id,
            ],
            type="test",
        ),
    ]

    assert tests == expected


@patch("builtins.open", mock_open(read_data=get_test_file("python")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_namespace_structure():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    tests = await file_parser.parse_file_structure("", patterns)

    expected = [
        File(id="", name="", file="", line=0, col=0, namespaces=[], type="file"),
        Test(
            id=tests[1].id,
            name="test_a",
            file="",
            line=4,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
        [
            Namespace(
                id=tests[2].id,
                name="TestAgain",
                file="",
                line=9,
                col=1,
                running=0,
                namespaces=[],
                type="namespace",
            ),
            Test(
                id=tests[3].id,
                name="test_d",
                file="",
                line=10,
                col=1,
                running=0,
                namespaces=["TestAgain-8458139203682520985"],
                type="test",
            ),
            Test(
                id=tests[4].id,
                name="test_a",
                file="",
                line=16,
                col=1,
                running=0,
                namespaces=["TestAgain-8458139203682520985"],
                type="test",
            ),
        ],
        [
            Namespace(
                id=tests[5].id,
                name="TestMyClass",
                file="",
                line=25,
                col=1,
                running=0,
                namespaces=[],
                type="namespace",
            ),
            Test(
                id=tests[6].id,
                name="test_d",
                file="",
                line=26,
                col=1,
                running=0,
                namespaces=["TestMyClass-8458139203682520985"],
                type="test",
            ),
            Test(
                id=tests[7].id,
                name="test_a",
                file="",
                line=29,
                col=1,
                running=0,
                namespaces=["TestMyClass-8458139203682520985"],
                type="test",
            ),
        ],
        Test(
            id=tests[8].id,
            name="test_b",
            file="",
            line=33,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
    ]

    assert tests.to_list() == expected
