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


class HeatIndex():
    def __init__(self):
        self.name = "HeatIndex Function"
        self.description = ""

    def getParameterInfo(self):
        return [
            {
                "name": "temperature",
                "dataType": 2,                  # raster
                "value": None,
                "displayName": "Temperature Raster",
                "description": "A single-band raster where pixel values represent ambient air temperature in Fahrenheit.",
                "required": True
            },
            {
                "name": "rh",
                "dataType": 2,                  # raster
                "value": None,
                "displayName": "Relative Humidity Raster",
                "description": "A single-band raster where pixel values represent relative humidity as a percentage value between 0 and 100.",
                "required": True
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          "referenceProperties": 2 | 4 | 8,                     # 
          "invalidatedProperties": 2 | 4 | 8                    # reset any statistics or histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def updateRasterInfo(self, **kwargs):
        kwargs["output_rasterInfo"]["bandCount"] = 1            # output is a single band raster
        kwargs["output_rasterInfo"]["statistics"] = ({"minimum": 0.0, "maximum": 180}, )  # we know something about the stats of the outgoing HeatIndex raster. 
        kwargs["output_rasterInfo"]["histogram"] = ()           # we know a nothing about the histogram of the outgoing raster.
        kwargs["output_rasterInfo"]["pixelType"] = "32_BIT_FLOAT"   # bit-depth of the outgoing HeatIndex raster based on user-specified parameters
        return kwargs

    def updatePixels(self, **pixelBlocks):
        t = np.array(pixelBlocks["temperature_pixelBlock"], dtype="float")
        r = np.array(pixelBlocks["rh_pixelBlock"], dtype="float")

        tr = t * r
        rr = r * r
        tt = t * t
        ttr = tt * r
        trr = t * rr
        ttrr = ttr * r

        output = -42.379 + (2.04901523 * t) + (10.14333127 * r) - (0.22475541 * tr) - (0.00683783 * tt) - (0.05481717 * rr) + (0.00122874 * ttr) + (0.00085282 * trr) - (0.00000199 * ttrr)
        np.copyto(pixelBlocks["output_pixelBlock"], output, casting="unsafe")
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata["datatype"] = "Scientific"
        elif bandIndex == 0:
            keyMetadata["wavelengthmin"] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata["wavelengthmax"] = None
            keyMetadata["bandname"] = "HeatIndex"
        return keyMetadata
