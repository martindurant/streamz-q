import asyncio
import queue
import streamz


class from_q(streamz.Source):
    """Source events from a threading.Queue, running another event framework

    Allows mixing of another event loop, for example pyqt, on another thread.

    """

    def __init__(self, q, sleep_time=0.01, **kwargs):
        """

        :param q: threading.Queue
            Any items pushed into here will become streamz events
        :param sleep_time: int
            Sets how long we wait before checking the input queue when
            empty (in s)
        :param kwargs:
            passed to streamz.Source
        """
        self.q = q
        self.sleep = sleep_time
        super().__init__(**kwargs)

    async def _run(self):
        """Poll threading queue for events

        This uses check-and-wait, but overhead is low. Could maybe have
        a sleep-free version with an threading.Event.
        """
        try:
            out = self.q.get_nowait()
            await self.emit(out, asynchronous=True)
        except queue.Empty:
            await asyncio.sleep(self.sleep)
