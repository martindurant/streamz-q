from PyQt5.QtWidgets import QApplication, QWidget
import streamz
import threading
import queue
import asyncio


class QueueWidget(QWidget):

    def __init__(self, q, **kwargs):
        self.q = q
        super().__init__(**kwargs)

    def mouseMoveEvent(self, *args):
        self.q.put(args)
        super().mouseMoveEvent(*args)

    def closeEvent(self, *args):
        self.q.put("DONE")
        super().closeEvent(*args)


def main_widget(q):
    app = QApplication([])
    w = QueueWidget(q)
    w.resize(250, 150)
    w.setWindowTitle('Simple')
    w.show()

    app.exec_()


class from_q(streamz.Source):
    """Source events from a threading.Queue, running another event framework

    Allows mixing of another event loop, for example pyqt, on another thread.

    """

    def __init__(self, q, sleep_time=0.01, **kwargs):
        self.q = q
        self.sleep = sleep_time
        super().__init__(**kwargs)

    async def _run(self):
        try:
            out = self.q.get_nowait()
            await self.emit(out, asynchronous=True)
        except queue.Empty:
            await asyncio.sleep(self.sleep)


if __name__ == '__main__':
    q = queue.Queue()
    s = from_q(q)
    s.timed_window(1).map(len).sink(print)
    s.start()
    main_widget(q)
