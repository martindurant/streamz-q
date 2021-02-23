import asyncio
import holoviews as hv
from holoviews.operation.datashader import rasterize
import numpy as np
import panel as pn
from panel.pane.holoviews import HoloViews
from streamz.sources import Source
import threading
import queue
import tornado.ioloop
hv.extension('bokeh')


class from_hv_selection(Source):
    def __init__(self, im, xcoords=None, ycoords=None, zcoords=None, scale="linear",
                 limits="percentile", vmin=5, vmax=95, colorbar=True,
                 cmap="gray", axes_names=None, select_type="box", **kwargs):

        nx, ny, *more = im.shape[::-1]
        xcoords = xcoords or np.arange(nx)
        ycoords = ycoords or np.arange(ny)
        self.polys = hv.Polygons([]).opts(alpha=0.1)
        cls = {"box": hv.streams.BoxEdit,
               "tap": hv.streams.PointerXY}
        self.stream = cls[select_type](source=self.polys)
        if more:
            zcoords = zcoords or np.arange(more[0])
            data = (xcoords, ycoords, zcoords, im)
            axes_names = axes_names or ["x", "y", "z"]
        else:
            data = (xcoords, ycoords, im)
            axes_names = axes_names or ["x", "y"]
        self.ds = hv.Dataset(data, axes_names, "Data")
        self.out = self.ds.to(hv.Image, axes_names[-2:]).opts(
            cmap=cmap, colorbar=colorbar,
            height=400, width=int(400 * len(xcoords) / len(ycoords))) #, cnorm=scale)
        self.stream.param.watch(self.cb, 'x')
        done = pn.widgets.Button(name="done")
        done.param.watch(self.stop, 'clicks')
        pl = HoloViews(self.out * self.polys)
        self.plot = pn.Column(pl, done)
        self.data = queue.Queue()
        super().__init__(**kwargs)

    def cb(self, *args):
        self.data.put((self.stream.x, self.stream.y))

    def mask(self):
        img = self.out.last if isinstance(self.out, hv.HoloMap) else self.out
        return rasterize(self.stream.element, target=img, aggregator='any',
                         dynamic=False)

    def start(self):
        super().start()
        self.server_loop = tornado.ioloop.IOLoop()
        self.server = pn.io.server.get_server(self.plot, start=False, show=True,
                                              loop=self.server_loop)
        thr = threading.Thread(target=self.server_loop.start)
        thr.daemon = True
        thr.start()
        self.server.start()

    def stop(self, *args):
        super().stop()
        self.loop.stop()

    async def _run(self):
        try:
            out = self.data.get_nowait()
            await self.emit(out, asynchronous=True)
        except queue.Empty:
            await asyncio.sleep(0.01)


if __name__ == "__main__":
    e = threading.Event()
    data = np.random.random((10, 10))
    loop = tornado.ioloop.IOLoop()
    s = from_hv_selection(data, select_type="tap", loop=loop, asynchronous=True)
    s = s.timed_window(1).map(len)
    s.sink(print)
    s.start()
    loop.start()
