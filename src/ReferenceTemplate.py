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


class ReferenceTemplate():
    def __init__(self):
        self.name = "NDVI Function"
        self.description = "NDVI Function"

        self.argumentinfo = [
            {
                "name": "raster",
                "datatype": 2,
                "value": "",
                "displayname": "Raster",
                "required": True
            },
            {
                "name": "red",
                "datatype": 0,
                "value": 1,
                "displayname": "Red Band ID",
                "required": True
            },
            {
                "name": "ir",
                "datatype": 0,
                "value": 2,
                "displayname": "Infrared Band ID",
                "required": True
            },
        ]

    def getconfiguration(self, **scalars):
        return {
          "extractbandids": (scalars["red"], scalars["ir"]),
          "compositerasters": False,
          "referenceproperties": 2 | 4
        }

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["bandcount"] = 1
        kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0.0, "maximum": 200.0}, )
        return kwargs

    def read(self, **kwargs):
        inblock = kwargs["raster_pixelblock"]
        red = np.array(inblock[0], dtype="float")
        ir = np.array(inblock[1], dtype="float")

        np.seterr(divide="ignore")

        outblock = np.multiply(np.divide((ir - red), (ir + red)), 100.0) + 100.0
        np.copyto(kwargs["output_pixelblock"], outblock, casting="unsafe")
        return kwargs

    def getproperty(self, name, defaultvalue, **kwargs):
        if name.lower == "datatype":
            return "Processed"
        else:
            return defaultvalue

    def getbandproperty(self, name, bandindex, defaultvalue, **kwargs):
        return defaultvalue
