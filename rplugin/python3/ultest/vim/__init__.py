from pynvim import Nvim
from .base import BaseVimClient
from .test import TestClient
from .buffers import BufferClient


class VimClient:
    """
    Client to interface with vim functions dealing with multi threading.
    """

    def __init__(self, vim: Nvim):
        self._vim = vim
        self._base = BaseVimClient(vim)
        self._test = TestClient(self._base)
        self._buffers = BufferClient(self._base)

        self.message = self._base.message
        self.schedule = self._base.schedule
        self.launch = self._base.launch
        self.call = self._base.call
        self.sync_call = self._base.sync_call
        self.command = self._base.construct_command
        self.sync_eval = self._base.sync_eval

    @property
    def buffers(self) -> BufferClient:
        return self._buffers

    @property
    def test(self) -> TestClient:
        return self._test
