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
#from scipy import ndimage


class MultidirectionalHillshade():
    def __init__(self):
        self.name = "Multidirectional Hillshade Function"
        self.description = ""
        self.referenceproperties = 4, 8

        self.argumentinfo = [
            {
                "name": "raster",
                "datatype": 2,
                "value": "",
                "displayname": "Raster",
                "required": True
            },
        ]

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["pixeltype"] = "8_BIT_UNSIGNED"
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0, "maximum": 3}, )
        kwargs["output_rasterinfo"]["nodata"] = 254
        return kwargs

    def read(self, **kwargs):
        inblock = np.array(kwargs["raster_pixelblock"], dtype="float")
        aa = inblock.astype(int);
        #k = np.array([[1,1,1],[1,1,0],[1,0,0]])
        #outblock = ndimage.convolve(inblock, k)
        np.copyto(kwargs["output_pixelblock"], aa, casting="unsafe")
        return kwargs
