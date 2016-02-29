import numpy as np


class Aggregate():

    def __init__(self):
        self.name = "Aggregate Rasters Function"
        self.description = "This function aggregates pixel values over a collection of overlapping single-band rasters."
        self.operator = np.sum

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': "Rasters",
                'description': "The collection of overlapping rasters to aggregate.",
            },
            {
                'name': 'method',
                'dataType': 'string',
                'value': 'Sum',
                'required': False,
                'displayName': "Method",
                'domain': ('Sum', 'Average', 'Median', 'Standard Deviation', 'Minimum', 'Maximum'),
                'description': "The method indicating how overlapping pixels of the input rasters are aggregated.",
            },
        ]

    def getConfiguration(self, **scalars):
        m = scalars.get('method', 'Sum').lower()
        if m == 'average':              self.operator = np.mean
        elif m == 'median':             self.operator = np.median
        elif m == 'minimum':            self.operator = np.min
        elif m == 'maximum':            self.operator = np.max
        elif m == 'standard deviation': self.operator = np.std
        else:                           self.operator = np.sum

        return {
            'inheritProperties': 4 | 8,             # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,          # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': True                       # need raster mask of all input rasters in .updatePixels().
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['resampling'] = False # process at native resolution
        kwargs['output_info']['pixelType'] = 'f4'   # output pixels are floating-point values
        kwargs['output_info']['noData'] = None      # we'll set the mask updatePixels()
        kwargs['output_info']['histogram'] = ()     # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # pixelBlocks['rasters_pixels']: tuple of 3-d array containing pixel blocks from each input raster
        # apply the selected operator over each array in the tuple
        outBlock = self.operator(pixelBlocks['rasters_pixels'], axis=0)
        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'], copy=False)
        masks = np.array(pixelBlocks['rasters_mask'], copy=False)
        pixelBlocks['output_mask'] = np.all(masks, axis=0).astype('u1', copy=False)
        return pixelBlocks
