import numpy as np
from skimage.transform import resize
from skimage.util import view_as_blocks
from skimage.filters import rank
from skimage.morphology import square


class RankFilter():

    def __init__(self):
        self.name = "Rank Filter Function"
        self.description = ("")
        self.func = rank.mean
        self.windowSize = 3

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ""
            },
            {
                'name': 'size',
                'dataType': 'numeric',
                'value': 5,
                'required': False,
                'displayName': "Window Size",
                'description': ("")
            },
            {
                'name': 'measure',
                'dataType': 'string',
                'value': 'Mean',
                'required': False,
                'displayName': "Measure",
                'domain': ('Minimum', 'Maximum', 'Mean', 'Bilateral Mean', 'Median', 
                           'Sum', 'Entropy', 'Threshold', 'Autolevel'),
                'description': ("")
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,             # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4 | 8,      # invalidate histogram, statistics, and key metadata
            'inputMask': True,
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['pixelType'] = 'f4'   # output pixels values are floating-point
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()

        self.windowSize = int(kwargs.get('size', 3))
        m = kwargs.get('measure', 'Mean').lower()

        if m == 'minimum':
            self.func = rank.minimum
        elif m == 'maximum':
            self.func = rank.maximum
        elif m == 'mean':
            self.func = rank.mean
        elif m == 'bilateral mean':
            self.func = rank.mean_bilateral
        elif m == 'median':
            self.func = rank.median
        elif m == 'sum':
            self.func = rank.sum
        elif m == 'entropy':
            self.func = rank.entropy
        elif m == 'threshold':
            self.func = rank.threshold
        elif m == 'autolevel':
            self.func = rank.autolevel
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        p = np.array(pixelBlocks['raster_pixels'], dtype='u1', copy=False)
        b = self.func(p, selem=square(self.windowSize), mask=pixelBlocks['raster_mask'])
        pixelBlocks['output_pixels'] = b.astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'
        return keyMetadata
