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
        self.applycolormap = False
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
            #{
            #    "name": "applycolormap",
            #    "datatype": 4,                  # boolean
            #    "value": self.applycolormap,
            #    "displayname": "Apply Colormap",
            #    "required": False
            #},
        ]

    def getconfiguration(self, **scalars):
        return {
          "extractbandids": (scalars["red"], scalars["ir"]),    # extract only the two bands corresponding to user-specified red and infrared band indexes.
          "compositerasters": False,                            # input is a single raster, band compositing doesn't apply.
          "referenceproperties": 2 | 4 | 8,                     # 
          "invalidatedproperties": 2 | 4 | 8                    # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def bind(self, **kwargs):
        #self.applycolormap = kwargs["applycolormap"]
              
        kwargs["output_rasterinfo"]["bandcount"] = 1            # output is a single band raster
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0.0, "maximum": 200.0}, )  # we know a little about the stats of the outgoing raster (scaled NDVI). 
        kwargs["output_rasterinfo"]["histogram"] = ()           # we know a nothing about the stats of the outgoing raster (scaled NDVI). 

        if (self.applycolormap):
            kwargs["output_rasterinfo"]["pixeltype"] = "8_BIT_UNSIGNED"
            kwargs["output_rasterinfo"]["colormap"] = (np.array([37, 39, 46, 49, 51, 52, 53, 54, 55, 57, 60, 61, 67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182], dtype="int32"),
                                                       np.array([255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 242, 234, 221, 208, 200, 187, 174, 162, 153, 140, 128, 255, 255, 115, 0, 102, 0, 89, 0, 72, 255, 55, 255, 34, 128, 8, 23, 33, 41, 46, 51, 54, 56, 59, 59, 59, 59, 56, 54, 48, 41, 33, 20, 8, 23, 33, 38, 41, 43, 46, 48, 48, 48, 46, 46, 41, 38, 36, 31, 23, 10, 26, 51, 68, 85, 98, 115, 128, 136, 149, 162, 174, 187, 195, 208, 217, 230, 242, 251, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 250, 242, 235, 227, 219, 212, 204, 196, 189, 181, 176, 168, 161, 156, 148, 140, 135, 128], dtype="uint8"),
                                                       np.array([161, 148, 138, 125, 112, 99, 84, 71, 54, 33, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 252, 0, 0, 0, 0, 255, 0, 255, 0, 255, 0, 128, 0, 0, 8, 31, 44, 59, 70, 85, 97, 109, 124, 134, 147, 160, 175, 191, 203, 219, 229, 247, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 251, 247, 238, 229, 221, 213, 208, 200, 191, 187, 179, 170, 166, 157, 149, 145, 136, 128, 125, 117, 109, 102, 95, 88, 82, 75, 69, 60, 56, 50, 43, 36, 30, 23, 16, 6], dtype="uint8"),
                                                       np.array([255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 255, 0, 255, 0, 255, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 251, 240, 225, 212, 198, 188, 171, 159, 148, 135, 123, 112, 94, 85, 72, 61, 42, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype="uint8"))
        else: 
            kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"
  
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
