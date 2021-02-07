import os
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue, Empty
from threading import Thread
from typing import Callable, List, Optional, Any, Union
import logging


class JobPriority(int, Enum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1


@dataclass(order=True)
class PrioritizedJob:
    priority: Union[JobPriority, int]
    func: Any = field(compare=False)


class JobManager:
    def __init__(self, num_threads: int = 0):
        if not num_threads:
            os_count = os.cpu_count()
            if os_count is not None:
                num_threads = max(1, os_count - 1)
            else:
                num_threads = 4
        self._queue: PriorityQueue[PrioritizedJob] = PriorityQueue()
        self._threads: List[Thread] = []
        self._running = True
        self._num_threads = num_threads
        self._start_workers(num_threads)
        logging.info(f"Using {num_threads} workers")

    def set_threads(self, num: int):
        self._start_workers(num)

    def run(self, func: Callable, priority: Union[int, JobPriority]):
        threaded = lambda: self._queue.put(PrioritizedJob(priority=priority, func=func))
        return threaded if self._threads else func

    def clear_jobs(self):
        self._running = False
        while not self._queue.empty():
            try:
                self._queue.get()
            except Empty:
                pass
        self._running = True

    def _stop_workers(self, timeout: Optional[float] = None):
        self._running = False
        for thread in self._threads:
            thread.join(timeout)

    def _start_workers(self, max_threads):
        self._stop_workers()
        self._running = True
        for _ in range(max_threads):
            thread = Thread(target=self._worker, daemon=True)
            thread.start()
            self._threads.append(thread)

    def _worker(self):
        while self._running:
            try:
                job = self._queue.get()
                job.func()
            except Exception as e:
                logging.exception(e)
