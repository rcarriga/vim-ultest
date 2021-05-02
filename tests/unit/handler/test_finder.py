from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest

from rplugin.python3.ultest.handler.finder import PositionFinder
from rplugin.python3.ultest.models import Namespace, Test
from rplugin.python3.ultest.models.namespace import Namespace
from tests.mocks import get_test_file

vim = Mock()
vim.launch = lambda f, _: f()
finder = PositionFinder(vim)


@patch("builtins.open", mock_open(read_data=get_test_file("python")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_find_python_tests():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    tests = list(await finder.find_all("", patterns))

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


@patch("builtins.open", mock_open(read_data=get_test_file("python")))
@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_namespace_structure():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    tests = await finder.find_all("", patterns)

    tests: Any = tests.to_list()
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
        [
            Namespace(
                id=tests[1][0].id,
                name="TestMock",
                file="",
                line=6,
                col=1,
                running=0,
                namespaces=[],
            ),
            Test(
                id=tests[1][1].id,
                name="test_a10",
                file="",
                line=7,
                col=1,
                running=0,
                namespaces=[tests[1][0].id],
            ),
        ],
        Test(
            id=tests[2].id,
            name="test_a43",
            file="",
            line=10,
            col=1,
            running=0,
            namespaces=[],
        ),
    ]

    assert tests == expected
