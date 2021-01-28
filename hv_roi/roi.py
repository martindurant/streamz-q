import holoviews as hv
from holoviews.operation.datashader import rasterize
import numpy as np
import panel as pn
from panel.pane.holoviews import HoloViews
hv.extension('bokeh')


class from_hv_selection:
    def __init__(self, im, xcoords=None, ycoords=None, zcoords=None, scale="linear",
                 limits="percentile", vmin=5, vmax=95, colorbar=True,
                 cmap="gray", axes_names=None, select_type="box"):

        nx, ny, *more = im.shape[::-1]
        xcoords = xcoords or np.arange(nx)
        ycoords = ycoords or np.arange(ny)
        self.polys = hv.Polygons([]).opts(alpha=0.1)
        cls = {"box": hv.streams.BoxEdit}
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
        done = pn.widgets.Button(name="done")
        # self.stream.param.watch(self.cb, 'data')
        done.param.watch(self.cb, 'clicks')
        pl = HoloViews(self.out * self.polys)
        self.plot = pn.Column(pl, done)

    def cb(self, *args):
        if self.stream.data["x1"]:
            self.loop.stop()

    def mask(self):
        img = self.out.last if isinstance(self.out, hv.HoloMap) else self.out
        return rasterize(self.stream.element, target=img, aggregator='any',
                         dynamic=False)

    def show(self):
        server = pn.io.server.get_server(self.plot, start=False, show=True)
        self.loop = server.io_loop.asyncio_loop
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        return #self.mask()
