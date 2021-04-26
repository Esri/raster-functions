import numpy as np


class Random():

    def __init__(self):
        self.name = "Random Raster Function"
        self.description = ""


    def getParameterInfo(self):
        return []


    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 0,                   # no input raster, nothing to inherit. 
          'invalidateProperties': 1 | 2 | 4 | 8,    # reset everything on the parent dataset.
          'resampling': True,
        }


    def updateRasterInfo(self, **kwargs):
        nBands = 3
        minX, minY, maxX, maxY = 0.0, 0.0, 1000.0, 1000.0
        dX, dY = 10.0, 10.0
        sr = 3857

        outputInfo = { 
            'bandCount': nBands,
            'pixelType': 'u1',
            'nativeExtent': (minX, minY, maxX, maxY),
            'extent': (minX, minY, maxX, maxY),
            'cellSize': (dX, dY),
            'spatialReference': sr,
            'nativeSpatialReference': sr,
            'statistics': (),
            'histogram': (),
            'colormap': (),
            'noData': np.array([256], dtype='u1'),
        }

        kwargs['output_info'] = outputInfo
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        outBlock = 255.0 * np.random.random_sample(shape)
        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        pixelBlocks['output_mask'] = np.ones(shape).astype('u1')
        return pixelBlocks
