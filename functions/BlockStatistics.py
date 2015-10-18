import numpy as np
from skimage.transform import resize
from skimage.util import view_as_blocks


class BlockStatistics():

    def __init__(self):
        self.name = "Block Statistics Function"
        self.description = ("Generates a downsampled output raster by computing a statistical "
                            "measure over non-overlapping square blocks of pixels in the input raster.")
        self.func = np.mean


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster over which block statistics is computed."
            },
            {
                'name': 'size',
                'dataType': 'numeric',
                'value': 1,
                'required': False,
                'displayName': "Block Size",
                'description': ("The number of pixels along each side of the square "
                                "non-overlapping block.")
            },
            {
                'name': 'measure',
                'dataType': 'string',
                'value': 'Mean',
                'required': False,
                'displayName': "Measure",
                'domain': ('Minimum', 'Maximum', 'Mean', 'Median', 'Sum', 'Nearest'),
                'description': ("The statistical measure computed over each "
                                "block of pixels in the input raster.")
            },
            {
                'name': 'factor',
                'dataType': 'numeric',
                'value': 1,
                'required': False,
                'displayName': "Downsampling Factor",
                'description': ("The integer factor by which the output raster is "
                                "downsampled relative to the input raster.")
            },
        ]


    def getConfiguration(self, **scalars):
        return { 
            'samplingFactor': scalars.get('size', 1.0),
            'inheritProperties': 4 | 8,             # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4 | 8,      # invalidate histogram, statistics, and key metadata
            'inputMask': True,
        }
        

    def updateRasterInfo(self, **kwargs):
        f = kwargs.get('factor', 1.0)
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['cellSize'] = tuple(np.multiply(kwargs['raster_info']['cellSize'], f))
        kwargs['output_info']['pixelType'] = 'f4'   # output pixels values are floating-point
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()

        m = kwargs.get('measure', 'Mean')
        if m.lower() == 'minimum':
            self.func = np.min
        elif m.lower() == 'maximum':
            self.func = np.max
        elif m.lower() == 'mean':
            self.func = np.mean
        elif m.lower() == 'median':
            self.func = np.median
        elif m.lower() == 'sum':
            self.func = np.sum
        elif m.lower() == 'nearest':
            self.func = None

        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        if self.func is None:
            b = resize(pixelBlocks['raster_pixels'], shape, order=0, preserve_range=True)
            m = resize(pixelBlocks['raster_mask'], shape, order=0, preserve_range=True)
        else:
            p = pixelBlocks['raster_pixels']
            blockSizes = tuple(np.divide(p.shape, shape))

            q = np.ma.masked_array(view_as_blocks(p, blockSizes), 
                                   view_as_blocks(~pixelBlocks['raster_mask'].astype('b1'), blockSizes))
            for i in range(len(q.shape) // 2):
                q = self.func(q, axis=-1)
            b = q.data
            m = ~q.mask

        pixelBlocks['output_pixels'] = b.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = m.astype('u1', copy=False)
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'
        return keyMetadata
