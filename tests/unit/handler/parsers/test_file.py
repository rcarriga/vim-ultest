from unittest.mock import Mock, patch

import pytest

from rplugin.python3.ultest.handler.parsers import FileParser
from rplugin.python3.ultest.models import Namespace, Test
from rplugin.python3.ultest.models.file import File
from rplugin.python3.ultest.models.namespace import Namespace
from tests.mocks import get_test_file

vim = Mock()
vim.launch = lambda f, _: f()
file_parser = FileParser(vim)


@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_python_tests():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    file_name = get_test_file("python")
    tests = list(await file_parser.parse_file_structure(file_name, patterns))

    expected = [
        File(
            id=file_name,
            name=file_name,
            file=file_name,
            line=0,
            col=0,
            namespaces=[],
            type="file",
        ),
        Test(
            id=tests[1].id,
            name="test_a",
            file=file_name,
            line=4,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
        Namespace(
            id=tests[2].id,
            name="TestAgain",
            file=file_name,
            line=9,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Test(
            id=tests[3].id,
            name="test_d",
            file=file_name,
            line=10,
            col=1,
            running=0,
            namespaces=[tests[2].id],
            type="test",
        ),
        Test(
            id=tests[4].id,
            name="test_a",
            file=file_name,
            line=16,
            col=1,
            running=0,
            namespaces=[tests[2].id],
            type="test",
        ),
        Namespace(
            id=tests[5].id,
            name="TestMyClass",
            file=file_name,
            line=25,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Test(
            id=tests[6].id,
            name="test_d",
            file=file_name,
            line=26,
            col=1,
            running=0,
            namespaces=[tests[5].id],
            type="test",
        ),
        Test(
            id=tests[7].id,
            name="test_a",
            file=file_name,
            line=29,
            col=1,
            running=0,
            namespaces=[tests[5].id],
            type="test",
        ),
        Test(
            id=tests[8].id,
            name="test_b",
            file=file_name,
            line=33,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
    ]

    assert tests == expected


@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_java_tests():
    patterns = {
        "test": [r"\v^\s*%(\zs\@Test\s+\ze)?%(\zspublic\s+\ze)?void\s+(\w+)"],
        "namespace": [r"\v^\s*%(\zspublic\s+\ze)?class\s+(\w+)"],
    }

    file_name = get_test_file("java")
    tests = list(await file_parser.parse_file_structure(file_name, patterns))

    expected = [
        File(
            id=file_name,
            name=file_name,
            file=file_name,
            line=0,
            col=0,
            running=0,
            namespaces=[],
            type="file",
        ),
        Namespace(
            id=tests[1].id,
            name="TestJunit1",
            file=file_name,
            line=5,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Test(
            id=tests[2].id,
            name="testPrintMessage",
            file=file_name,
            line=11,
            col=1,
            running=0,
            namespaces=[tests[1].id],
            type="test",
        ),
    ]

    assert tests == expected


@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_jest_tests():
    patterns = {
        "test": [r'\v^\s*%(it|test)\s*[( ]\s*%("|' '|`)(.*)%("|' "|`)"],
        "namespace": [
            r'\v^\s*%(describe|suite|context)\s*[( ]\s*%("|' '|`)(.*)%("|' "|`)"
        ],
    }

    file_name = get_test_file("jest")
    tests = list(await file_parser.parse_file_structure(file_name, patterns))

    expected = [
        File(
            id=file_name,
            name=file_name,
            file=file_name,
            line=0,
            col=0,
            running=0,
            namespaces=[],
            type="file",
        ),
        Namespace(
            id=tests[1].id,
            name='First namespace", () => {',
            file=file_name,
            line=1,
            col=1,
            running=0,
            namespaces=[],
            type="namespace",
        ),
        Namespace(
            id=tests[2].id,
            name='Second namespace", () => {',
            file=file_name,
            line=2,
            col=1,
            running=0,
            namespaces=[tests[1].id],
            type="namespace",
        ),
        Test(
            id=tests[3].id,
            name="it shouldn't pass\", () => {",
            file=file_name,
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


@patch("os.path.isfile", lambda _: True)
@pytest.mark.asyncio
async def test_parse_namespace_structure():
    patterns = {
        "test": [r"\v^\s*%(async )?def (test_\w+)"],
        "namespace": [r"\v^\s*class (\w+)"],
    }

    file_name = get_test_file("python")
    tests = await file_parser.parse_file_structure(file_name, patterns)

    expected = [
        File(
            id=file_name,
            name=file_name,
            file=file_name,
            line=0,
            col=0,
            namespaces=[],
            type="file",
        ),
        Test(
            id=tests[1].id,
            name="test_a",
            file=file_name,
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
                file=file_name,
                line=9,
                col=1,
                running=0,
                namespaces=[],
                type="namespace",
            ),
            Test(
                id=tests[3].id,
                name="test_d",
                file=file_name,
                line=10,
                col=1,
                running=0,
                namespaces=[tests[2].id],
                type="test",
            ),
            Test(
                id=tests[4].id,
                name="test_a",
                file=file_name,
                line=16,
                col=1,
                running=0,
                namespaces=[tests[2].id],
                type="test",
            ),
        ],
        [
            Namespace(
                id=tests[5].id,
                name="TestMyClass",
                file=file_name,
                line=25,
                col=1,
                running=0,
                namespaces=[],
                type="namespace",
            ),
            Test(
                id=tests[6].id,
                name="test_d",
                file=file_name,
                line=26,
                col=1,
                running=0,
                namespaces=[tests[5].id],
                type="test",
            ),
            Test(
                id=tests[7].id,
                name="test_a",
                file=file_name,
                line=29,
                col=1,
                running=0,
                namespaces=[tests[5].id],
                type="test",
            ),
        ],
        Test(
            id=tests[8].id,
            name="test_b",
            file=file_name,
            line=33,
            col=1,
            running=0,
            namespaces=[],
            type="test",
        ),
    ]

    assert tests.to_list() == expected
