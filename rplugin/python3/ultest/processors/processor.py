from abc import ABC, abstractmethod, abstractproperty

from ultest.models import Test, Result
from ultest.vim import VimClient


class Processor(ABC):
    def __init__(self, vim: VimClient):
        self._vim = vim

    @abstractproperty
    def condition(self) -> bool:
        """
        Check a condition to determine if this processor is being used.

        @rtype: bool
        """

    @abstractmethod
    def clear(self, test: Test, sync: bool = True):
        """
        Clear a test from a processor.

        :param test: Test to clear
        :type test: Test
        :param sync: Run synchronously (Must be called from main thread), defaults to True
        :type sync: bool, optional
        """

    @abstractmethod
    def start(self, test: Test, sync: bool = True):
        """
        Pass a test to processor on starting test.

        :param test: Test to clear
        :type test: Test
        :param sync: Run synchronously (Must be called from main thread), defaults to True
        :type sync: bool, optional
        """

    @abstractmethod
    def exit(self, result: Result, sync: bool = True):
        """
        Pass a test to processor on test finishing.

        :param result: Test to clear
        :type result: Result
        :param sync: Run synchronously (Must be called from main thread), defaults to True
        :type sync: bool, optional
        """
