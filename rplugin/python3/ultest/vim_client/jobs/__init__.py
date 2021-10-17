import asyncio
import sys
import traceback
from asyncio import CancelledError, Event, Semaphore
from asyncio.events import AbstractEventLoop
from collections import defaultdict
from threading import Thread
from typing import Coroutine, Dict
from uuid import uuid4

from ...logging import get_logger

logger = get_logger()


class JobManager:
    def __init__(self, num_threads: int = 2):
        self._jobs: defaultdict[str, Dict[str, Event]] = defaultdict(dict)
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        if sys.version_info < (3, 8):
            # Use the new default watcher from  >= 3.8, implemented locally
            # https://bugs.python.org/issue35621
            from .watcher import ThreadedChildWatcher

            logger.info("Using local threaded child watcher")
            asyncio.set_child_watcher(ThreadedChildWatcher())
            self._sem = Semaphore(num_threads, loop=self._loop)
        else:
            self._sem = Semaphore(num_threads)

    @property
    def semaphore(self) -> Semaphore:
        return self._sem

    def run(self, cor: Coroutine, job_group: str):
        job_id = str(uuid4())
        cancel_event = Event(loop=self._loop)
        wrapped_cor = self._handle_coroutine(
            cor, job_group=job_group, job_id=job_id, cancel_event=cancel_event
        )
        asyncio.run_coroutine_threadsafe(wrapped_cor, loop=self._loop)
        self._jobs[job_group][job_id] = cancel_event

    def stop_jobs(self, group: str) -> bool:
        logger.finfo("Stopping jobs in group {group}")
        cancel_events = self._jobs[group]
        if not cancel_events:
            logger.finfo("No jobs found for group {group}")
            return False
        for cancel_event in cancel_events.values():
            self._loop.call_soon_threadsafe(cancel_event.set)
        return True

    async def _handle_coroutine(
        self, cor: Coroutine, job_group: str, job_id: str, cancel_event: Event
    ):
        try:
            logger.fdebug("Starting job with group {job_group}")
            run_task = asyncio.create_task(cor)
            cancel_task = asyncio.create_task(cancel_event.wait())
            try:
                done, _ = await asyncio.wait(
                    [run_task, cancel_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except CancelledError:
                logger.exception(f"Task was cancelled prematurely {run_task}")
            else:
                if run_task in done:
                    e = run_task.exception()
                    if e:
                        logger.warn(f"Exception throw in job: {e}")
                        logger.warn(
                            "\n".join(
                                traceback.format_exception(type(e), e, e.__traceback__)
                            )
                        )
                    logger.fdebug("Finished job with group {job_group}")
                else:
                    run_task.cancel()
                    logger.fdebug("Cancelled running job with group {job_group}")
        except CancelledError:
            logger.exception("Job runner cancelled")
            raise
        except Exception:
            logger.exception("Error running job")
        finally:
            self._jobs[job_group].pop(job_id)
