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
        self.description = "Aggregation Function"

        self.argumentinfo = [
            {
                "name": "rasters",
                "datatype": 3,                  # multiple rasters
                "value": "",
                "displayname": "Rasters",
                "required": True
            },
        ]

    def getconfiguration(self, **scalars):
        return {
          "compositerasters": False,            # don't want to composite all bands of all input rasters
          "referenceproperties": 2 | 4          # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"   # output pixels are floating-point values
        return kwargs

    def read(self, **kwargs):
        inblocks = kwargs["rasters_pixelblock"]                 # get a tuple of pixel blocks where each element is...  
        n = len(inblocks)                                       # ...a numpy array corresponding to the pixel block of an input raster
        if (n < 1):
          raise Exception("No input rasters provided.")

        outblock = np.array(inblocks[0], dtype="float")         # initialize output pixel block with the first input block
        for i in range(1, n):                                   # add each subsequent input block to our local output array
          block = np.array(inblocks[i], dtype="float")
          outblock = np.add(outblock, block)

        np.copyto(kwargs["output_pixelblock"], outblock, casting="unsafe")  # copy local array to output pixel block.  
        return kwargs
