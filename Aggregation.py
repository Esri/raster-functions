"""
COPYRIGHT 1995-2004 ESRI

TRADE SECRETS: ESRI PROPRIETARY AND CONFIDENTIAL
Unpublished material - all rights reserved under the
Copyright Laws of the United States.

For additional information, contact:
Environmental Systems Research Institute, Inc.
Attn: Contracts Dept
380 New York Street
redlands, California, USA 92373
email: contracts@esri.com
"""

import numpy as np


class Aggregation():
    def __init__(self):
        self.name = "Aggregation Function"
        self.description = "Aggregates pixel values of a collection of overlapping rasters."

    def getParameterInfo(self):
        return [{
                'name': 'rasters',
                'dataType': 3,                                      # multiple rasters
                'value': None,
                'displayName': 'Rasters',
                'required': True,
                'description': 'The set of rasters to aggregate.',
            },]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,                           # inherit everything but the pixel type (1)
          'invalidateProperties': 2 | 4                             # invalidate histogram and statistics because we are modifying pixel values
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['pixelType'] = '32_BIT_FLOAT'         # output pixels are floating-point values
        return kwargs

    def updatePixels(self, **pixelBlocks):
        inBlocks = pixelBlocks['rasters_pixels']                    # get a tuple of pixel blocks where each element is...
        n = len(inBlocks)                                           # ...a numpy array corresponding to the pixel block of an input raster
        if (n < 1):
          raise Exception("No input rasters provided.")

        outBlock = np.array(inBlocks[0], dtype='float')             # initialize output pixel block with the first input block
        for i in range(1, n):                                       # add each subsequent input block to our local output array
          outBlock = outBlock + np.array(inBlocks[i], dtype='float')

        np.copyto(pixelBlocks['output_pixels'], outBlock, casting='unsafe')  # copy local array to output pixel block.
        return pixelBlocks
