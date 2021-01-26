
class from_hv_selection:
    def __init__(self, im, xcoords=None, ycoords=None, zcoords=None, scale="linear",
                 limits="percentile", vmin=5, vmax=95, colorbar=True,
                 cmap="grey", axes_names=None, select_type="box"):
        import numpy as np
        import holoviews as hv
        from panel.pane.holoviews import HoloViews
        from holoviews import streams

        nx, ny, *more = im.shape[::-1]
        xcoords = xcoords or np.arange(nx)
        ycoords = ycoords or np.arange(ny)
        self.polys = hv.Polygons([])
        cls = {"box": streams.BoxEdit}
        self.stream = cls[select_type](source=self.polys)
        if more:
            zcoords = zcoords or np.arange(more[0])
            data = (xcoords, ycoords, zcoords, im)
            axes_names = axes_names or ["x", "y", "z"]
        else:
            data = (xcoords, ycoords, im)
            axes_names = axes_names or ["x", "y"]
        self.ds = hv.Dataset(data, axes_names, "Data")
        self.out = self.ds.to(hv.Image, axes_names[-2:])
        self.plot = HoloViews(self.out * self.polys)

    def mask(self):
        import holoviews as hv
        from holoviews.operation.datashader import rasterize
        img = self.out.last if isinstance(self.out, hv.HoloMap) else self.out
        return rasterize(self.stream.element, target=img, aggregator='any',
                         dynamic=False)

    def show(self):
        try:
            self.plot.show()
        except KeyboardInterrupt:
            pass

