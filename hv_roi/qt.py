from PyQt5.QtWidgets import QApplication, QWidget
import queue
from hv_roi.plugin import from_q


class QueueWidget(QWidget):
    """Simplest possible widget, passing drag events to a given Queue"""

    def __init__(self, q, **kwargs):
        self.q = q
        super().__init__(**kwargs)

    def mouseMoveEvent(self, *args):
        self.q.put(args)
        super().mouseMoveEvent(*args)


def main_widget(q):
    app = QApplication([])
    w = QueueWidget(q)
    w.resize(250, 150)
    w.show()
    app.exec_()


if __name__ == '__main__':
    q = queue.Queue()
    s = from_q(q)
    s.timed_window(1).map(len).sink(print)
    s.start()
    main_widget(q)
    s.stop()
