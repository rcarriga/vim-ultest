from pynvim import Nvim

from ultest.handler.base import Handler
from ultest.handler.positions import Positions
from ultest.handler.results import Results
from ultest.handler.runner import Runner
from ultest.processors import Processors
from ultest.vim import VimClient


def create(vim: Nvim) -> Handler:
    client = VimClient(vim)
    processors = Processors(client)
    positions = Positions(client)
    runner = Runner(client, processors)
    results = Results(client, processors)
    return Handler(client, runner, positions, results)
