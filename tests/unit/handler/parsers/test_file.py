from typing import Any
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
        File(id="", name="", file=""),
        Test(
            id=tests[1].id,
            name="test_a30",
            file="",
            line=3,
            col=1,
            running=0,
            namespaces=[],
        ),
        Namespace(
            id=tests[2].id,
            name="TestMock",
            file="",
            line=6,
            col=1,
            running=0,
            namespaces=[],
        ),
        Test(
            id=tests[3].id,
            name="test_a10",
            file="",
            line=7,
            col=1,
            running=0,
            namespaces=[tests[2].id],
        ),
        Test(
            id=tests[4].id,
            name="test_a43",
            file="",
            line=12,
            col=1,
            running=0,
            namespaces=[],
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

    tests: Any = tests.to_list()
    expected = [
        File(id="", name="", file=""),
        Test(
            id=tests[1].id,
            name="test_a30",
            file="",
            line=3,
            col=1,
            running=0,
            namespaces=[],
        ),
        [
            Namespace(
                id=tests[2][0].id,
                name="TestMock",
                file="",
                line=6,
                col=1,
                running=0,
                namespaces=[],
            ),
            Test(
                id=tests[2][1].id,
                name="test_a10",
                file="",
                line=7,
                col=1,
                running=0,
                namespaces=[tests[2][0].id],
            ),
        ],
        Test(
            id=tests[3].id,
            name="test_a43",
            file="",
            line=12,
            col=1,
            running=0,
            namespaces=[],
        ),
    ]

    assert tests == expected
