from unittest import TestCase
from unittest.mock import Mock, call, mock_open, patch

from rplugin.python3.ultest.handler.runner.handle import ProcessIOHandle


@patch("ultest.handler.runner.handle.os")
class TestUltestProcess(TestCase):
    def test_open_keeps_input_open(self, _):
        handle = ProcessIOHandle(in_path="in", out_path="out")
        m_open = mock_open()
        with patch("ultest.handler.runner.handle.open", m_open):
            with handle.open() as (in_, out_):
                self.assertIn(call("in", "wb"), m_open.mock_calls)
                in_.close.assert_not_called()
            in_.close.assert_called()

    def test_open_cleans_up_input(self, mock_os: Mock):
        handle = ProcessIOHandle(in_path="in", out_path="out")
        m_open = mock_open()
        mock_os.path.exists.return_value = False
        with patch("ultest.handler.runner.handle.open", m_open):
            with handle.open() as (in_, out_):
                mock_os.remove.assert_not_called()
            mock_os.remove.assert_called_with("in")

    def test_open_preserves_output(self, mock_os: Mock):
        handle = ProcessIOHandle(in_path="in", out_path="out")
        m_open = mock_open()
        mock_os.path.exists.return_value = False
        with patch("ultest.handler.runner.handle.open", m_open):
            with handle.open() as (in_, out_):
                ...
            self.assertNotIn(call("out"), mock_os.remove.mock_calls)
