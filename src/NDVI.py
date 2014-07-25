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


class NDVI():
    def __init__(self):
        self.name = "NDVI Function"
        self.description = "Computes Normalized Difference Vegetation Index given a raster's Red and Infrared band. Output's NDVI value scaled to [0, 200]."

        self.argumentinfo = [
            {
                "name": "raster",
                "datatype": 2,                  # raster
                "value": "",
                "displayname": "Raster",
                "required": True
            },
            {
                "name": "red",
                "datatype": 0,                  # numeric
                "value": 1,
                "displayname": "Red Band ID",
                "required": True
            },
            {
                "name": "ir",
                "datatype": 0,                  # numeric
                "value": 2,
                "displayname": "Infrared Band ID",
                "required": True
            },
        ]

    def getconfiguration(self, **scalars):
        return {
          "extractbandids": (scalars["red"], scalars["ir"]),    # extract only the two bands corresponding to user-specified red and infrared band indexes.
          "compositerasters": False,                            # input is a single raster, band compositing doesn't apply.
          "referenceproperties": 2 | 4                          # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["bandcount"] = 1            # output is a single band raster
        kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"   # ... with floating-point pixel values.
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0.0, "maximum": 200.0}, )  # we know a little about the stats of the outgoing raster (scaled NDVI). 
        return kwargs

    def read(self, **kwargs):
        inblock = kwargs["raster_pixelblock"]                   # get the input raster pixel block.
        red = np.array(inblock[0], dtype="float")               # extractbandids ensures first band is Red.
        ir = np.array(inblock[1], dtype="float")                # extractbandids ensures second band is Infrared.

        np.seterr(divide="ignore")

        outblock = np.multiply(np.divide((ir - red), (ir + red)), 100.0) + 100.0        # scale and offset the NDVI value (ir-red)/(ir+red).
        np.copyto(kwargs["output_pixelblock"], outblock, casting="unsafe")              # copy local array to output pixel block.
        return kwargs

    def getproperty(self, name, defaultvalue, **kwargs):
        if name.lower == "datatype":                            # outgoing raster is now 'Processed'.
            return "Processed"
        else:
            return defaultvalue

    def getallproperties(self, **args):
        args["datatype"] = "Processed"                          # outgoing raster is now 'Processed'.
        return args 
