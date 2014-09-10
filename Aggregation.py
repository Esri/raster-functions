import numpy as np


class Aggregation():

    def __init__(self):
        self.name = "Aggregation Function"
        self.description = "This function computes the sum of pixel values over a collection of overlapping single-band rasters."


    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': "Rasters",
                'description': "The set of rasters to aggregate.",
            },
        ]


    def getConfiguration(self, **scalars):
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
            outBlock = np.sum(inBlock, axis=0)

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks
