import numpy as np
from skimage.transform import resize
from skimage.util import view_as_blocks
from skimage.filters import rank
from skimage.morphology import square
from utils import Trace


class RankFilter():

    def __init__(self):
        self.name = "Rank Filter Function"
        self.description = ("")
        self.func = rank.mean
        self.window = None
        self.trace = Trace()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster on which the filter is applied."
            },
            {
                'name': 'measure',
                'dataType': 'string',
                'value': 'Mean',
                'required': False,
                'displayName': "Measure",
                'domain': ('Minimum', 'Maximum', 'Mean', 'Bilateral Mean', 'Median', 
                           'Sum', 'Entropy', 'Threshold', 'Autolevel'),
                'description': ("The measure represented by an ouput pixel " 
                                "computed over a sliding window of input pixels.")
            },
            {
                'name': 'size',
                'dataType': 'numeric',
                'value': 5,
                'required': False,
                'displayName': "Window Size",
                'description': ("The width of the sliding window or kernel (in pixels).")
            },
            {
                'name': 'res',
                'dataType': 'string',
                'value': 'Request',
                'required': False,
                'displayName': "Resolution",
                'domain': ('Request', 'Raster'),
                'description': ("The resolution at which the filter is applied. "
                                "Choose between processing input pixels at resampled display/request resolution "
                                "or in the original/raster resolution.")
            },
        ]

    def getConfiguration(self, **scalars):
        r = scalars.get('res', None)

        return {
            'inheritProperties': 4 | 8,             # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4 | 8,      # invalidate histogram, statistics, and key metadata
            'inputMask': True,
            'resampling': not(r is not None and str(r).lower() == 'raster')
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()

        self.window = square(int(kwargs.get('size', 3)))
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
        p = pixelBlocks['raster_pixels']
        m = pixelBlocks['raster_mask']

        q = np.empty(p.shape)
        for b in range(p.shape[0]): 
            q[b] = self.func(p[b], selem=self.window, mask=m[b])

        pixelBlocks['output_pixels'] = q.astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'
        return keyMetadata


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1] Sicuranza, G., 2000. Nonlinear image processing. Academic Press.

    [2] Rank Filters for Image Processing.
        http://www.numerical-tours.com/matlab/denoisingadv_7_rankfilters/

    [3] Scikit-image: Image processing in Python (Rank filters).
        http://scikit-image.org/docs/dev/auto_examples/applications/plot_rank_filters.html
"""
