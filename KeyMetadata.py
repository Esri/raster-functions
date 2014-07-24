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


class KeyMetadata():
    def __init__(self):
        self.name = "Key Metadata"
        self.description = "Key Metadata"

        self.argumentinfo = [
            {
                "name": "raster",
                "datatype": 2,
                "value": "",
                "displayname": "Raster",
                "required": True
            },
        ]

    def getconfiguration(self, **scalars):
        return { 
            "referenceproperties": 8
        }

    def getproperty(self, name, defaultvalue, **args):
        s = name.lower()
        if s == "datatype":
            return "Processed"
        elif s == "cloudcover":
            return 50.0
        else:
            return defaultvalue

    def getallproperties(self, **args):
        args["datatype"] = "Processed"
        args["cloudcover"] = 50.0
        return args

    def getbandproperty(self, name, bandindex, defaultvalue, **args):
        s = name.lower()
        if bandindex == 0:
            if s == "wavelengthmin":
                return 400
            elif s == "wavelengthmax":
                return 600
        return defaultvalue
