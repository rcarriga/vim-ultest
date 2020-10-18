from queue import Queue
from threading import Thread
from typing import Callable, List


class Threader:
    def __init__(self):
        self._queue: "Queue[Callable]" = Queue()
        self._threads: List[Thread] = []
        self._running = True
        self._start_workers(2)

    def set_threads(self, num: int):
        self._start_workers(num)

    def run(self, func: Callable):
        threaded = lambda: self._queue.put(func)
        return threaded if self._threads else func

    def _stop_workers(self):
        self._running = False
        for thread in self._threads:
            thread.join()

    def _start_workers(self, max_threads):
        self._stop_workers()
        self._running = True
        for _ in range(max_threads):
            thread = Thread(target=self._worker, daemon=True)
            thread.start()
            self._threads.append(thread)

    def _worker(self):
        while self._running:
            func = self._queue.get()
            func()
