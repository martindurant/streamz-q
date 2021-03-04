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
        im = np.random.random((10, 10))
        nx, ny = im.shape
        xcoords = np.arange(nx)
        ycoords = np.arange(ny)
        self.polys = hv.Polygons([]).opts(alpha=0.1)
        self.stream = hv.streams.PointerXY(source=self.polys)
        data = (xcoords, ycoords, im)
        axes_names = ["x", "y"]
        self.ds = hv.Dataset(data, axes_names, "Data")
        self.out = self.ds.to(hv.Image, axes_names[-2:]).opts(
            height=400, width=int(400 * len(xcoords) / len(ycoords)))
        self.stream.param.watch(self.cb, 'x')
        done = pn.widgets.Button(name="done")
        done.param.watch(self.stop, 'clicks')
        pl = HoloViews(self.out * self.polys)
        self.plot = pn.Column(pl, done)
        self.q = q

    def cb(self, *args):
        self.q.put((self.stream.x, self.stream.y))

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
    s = s.timed_window(1).map(len)
    s.sink(print)
    s.start()
    widget.start()
