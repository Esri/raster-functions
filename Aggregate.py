import numpy as np


class Aggregate():

    def __init__(self):
        self.name = "Aggregate Rasters Function"
        self.description = "This function computes the sum of pixel values over a collection of overlapping single-band rasters."
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
        if m == 'average':
            self.operator = np.mean
        elif m == 'median':
            self.operator = np.median
        elif m == 'minimum':
            self.operator = np.min
        elif m == 'maximum':
            self.operator = np.max
        elif m == 'standard deviation':
            self.operator = np.std
        else:
            self.operator = np.sum

        return {
            'compositeRasters': True,            
            'inheritProperties': 4 | 8,             # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,          # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': False                      # Don't need input raster mask in .updatePixels(). 
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['pixelType'] = 'f4'   # output pixels are floating-point values
        kwargs['output_info']['bandCount'] = 1      # output raster is single-band aggregate
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        inBlock = pixelBlocks['composite_pixels']

        if len(inBlock.shape) <= 2 or inBlock.shape[0] == 1:
            outBlock = inBlock
        else:
            outBlock = self.operator(inBlock, axis=0)

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks

