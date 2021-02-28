import asyncio
from asyncio import AbstractEventLoop, CancelledError, Event
from collections import defaultdict
from threading import Thread
from typing import Coroutine, Dict
from uuid import uuid4

from ..logging import UltestLogger


class ThreadSafeEvent(Event):
    def __init__(self, loop: AbstractEventLoop):
        self.thread_loop = loop
        super().__init__()

    def set(self):
        self.thread_loop.call_soon_threadsafe(super().set)


class JobManager:
    def __init__(self, logger: UltestLogger, num_threads: int = 2):
        self._logger = logger
        self._jobs: defaultdict[str, Dict[str, Event]] = defaultdict(dict)
        self._loop = asyncio.get_event_loop()
        self._thread = Thread(target=self._loop.run_forever, daemon=True)
        self._sem = asyncio.Semaphore(num_threads)
        self._thread.start()

    def run(self, cor: Coroutine, job_group: str):
        job_id = str(uuid4())
        cancel_event = ThreadSafeEvent(loop=self._loop)
        wrapped_cor = self._handle_coroutine(
            cor, job_group=job_group, job_id=job_id, cancel_event=cancel_event
        )
        asyncio.run_coroutine_threadsafe(wrapped_cor, loop=self._loop)
        self._jobs[job_group][job_id] = cancel_event

    def stop_jobs(self, group: str):
        self._logger.fdebug("Stopping jobs in group {group}")
        for cancel_event in self._jobs[group].values():
            cancel_event.set()

    async def _handle_coroutine(
        self, cor: Coroutine, job_group: str, job_id: str, cancel_event: Event
    ):
        try:
            async with self._sem:
                self._logger.fdebug("Starting job with group {job_group}")
                run_task = asyncio.create_task(cor)
                cancel_task = asyncio.create_task(cancel_event.wait())
                try:
                    done, _ = await asyncio.wait(
                        [run_task, cancel_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                except CancelledError:
                    self._logger.exception(f"Task was cancelled prematurely {run_task}")
                else:
                    if run_task in done:
                        self._logger.fdebug("Finished job with group {job_group}")
                    else:
                        run_task.cancel()
                        self._logger.fdebug(
                            "Cancelled running job with group {job_group}"
                        )
        except CancelledError:
            self._logger.exception("Job runner cancelled")
            raise
        except Exception:
            self._logger.exception("Error running job")
        finally:
            self._jobs[job_group].pop(job_id)
