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
        self.description = "Override key metadata in a function chain."

        self.argumentinfo = [
            {
                "name": "raster",
                "datatype": 2,                  # raster
                "value": "",
                "displayname": "Raster",
                "required": True,
                "description": "The primary raster input."
            },
            {
                "name": "property",
                "datatype": 1,                  # string
                "value": "",
                "displayname": "Property",
                "required": False,
                "description": "The name of the optional key metadata to override."
            },
            {
                "name": "value",
                "datatype": 1,                  # string
                "value": "",
                "displayname": "Value",
                "required": False,
                "description": "The overriding new value of the key metadata."
            }
        ]

    def getconfiguration(self, **scalars):
        return { 
            "referenceproperties": 8            # reset any key properties held by the parent function raster dataset
        }

    def bind(self, **kwargs):
        self.propertyName = kwargs["property"]  # remember these user-specified scalar inputs
        self.propertyValue = kwargs["value"]
        return kwargs

    def getproperty(self, name, defaultvalue, **kwargs):
        s = name.lower()
        if s == self.propertyName:              # return user-specified value associated with this user-specified key property
            return self.propertyValue
        elif s == "datatype":                   # overriding a specific key property
            return "Processed"
        elif s == "cloudcover":
            return 0.0
        else:
            return defaultvalue

    def getallproperties(self, **kwargs):       # overriding applicable key properties when requested in bulk
        kwargs["datatype"] = "Processed"
        kwargs["cloudcover"] = 50.0
        if len(self.propertyName) > 0:
            kwargs[self.propertyName] = self.propertyValue
        return kwargs

    def getbandproperty(self, name, bandindex, defaultvalue, **kwargs): # overriding band-specific key property
        s = name.lower()
        if bandindex == 0:
            if s == "wavelengthmin":
                return 400
            elif s == "wavelengthmax":
                return 600
        return defaultvalue

    def getallbandproperties(self, bandindex, **kwargs):    # overriding band-specific key properties when requested in bulk
        s = name.lower()
        if bandindex == 0:
            kwargs["wavelengthmin"] = 400
            kwargs["wavelengthmax"] = 600
        return kwargs
