import holoviews as hv
import numpy as np
import panel as pn
from panel.pane.holoviews import HoloViews
import queue
import tornado.ioloop
from streamz_q.plugin import from_q
hv.extension('bokeh')


class hv_widget:
    """Simple holoviews plot widget passing move events to a given Queue"""

    def __init__(self, q):
        self.polys = hv.Polygons([]).opts(alpha=0.1)
        self.stream = hv.streams.PointerXY(source=self.polys)
        self.stream.param.watch(self.cb, 'x')
        self.overlay = np.zeros((100, 100))
        done = pn.widgets.Button(name="done")
        done.param.watch(self.stop, 'clicks')
        self.Time = hv.streams.Stream.define('Time', time=1.0)
        self.counter = 0
        self.dmap = hv.DynamicMap(self._dmap, streams=[self.Time()])
        pl = HoloViews((self.polys *
                       self.dmap.opts(height=400, width=400, cmap='Category10')).opts(
            xlim=(1, 99), ylim=(1, 99)
        ))
        self.plot = pn.Column(pl, done)
        self.q = q

    def cb(self, *args):
        self.q.put((self.stream.x, self.stream.y))

    def _dmap(self, **args):
        return hv.Image(self.overlay, bounds=(0, 0, 100, 100)).opts(clim=(0, 9))

    def set_overlay(self, data):
        if data:
            mask = list(zip(*data))
            mask = 100 - np.array(mask[1], dtype=int), np.array(mask[0], dtype=int)
            self.overlay[mask] += 1
            counter = self.counter
            self.server_loop.add_callback(lambda: self.dmap.event(time=counter))
            self.counter += 1

    def stop(self, *args):
        self.server.stop()
        self.server_loop.stop()

    def start(self):
        self.server_loop = tornado.ioloop.IOLoop()
        self.server = pn.io.server.get_server(self.plot, start=False, show=True,
                                              loop=self.server_loop)
        self.server_loop.start()


if __name__ == "__main__":
    q = queue.Queue()
    widget = hv_widget(q)
    s = from_q(q)
    s = s.timed_window(1)
    s.sink(widget.set_overlay)
    s.map(len).sink(print)
    s.start()
    widget.start()
