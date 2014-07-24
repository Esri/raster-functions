"""
COPYRIGHT 1995-2004 ESRI

TRADE SECRETS: ESRI PROPRIETARY AND CONFIDENTIAL
Unpublished material - all rights reserved under the
Copyright Laws of the United States.

For additional information, contact:
Environmental Systems Research Institute, Inc.
Attn: Contracts Dept
380 New York Street
Redlands, California, USA 92373
email: contracts@esri.com
"""
#Note: This raster function requires the prefer max to be larger than 1.
#This function reads depth value from input raster's corresponding StdZ field
import numpy as np


class FishHabitatSuitabilityDepth():
    def __init__(self):
        self.name = "FishHabitatSuitabilityDepth Function"
        self.description = "FishHabitatSuitabilityDepth Function"
        self.depthval = "0"

        #Define function parameters
        self.argumentinfo = [{
                "name": "temperature",
                "datatype": 2,
                "value": "",
                "displayname": "Surface Temperature",
                "required": True
            },
            {
                "name": "salinity",
                "datatype": 2,
                "value": "",
                "displayname": "Surface Sanility",
                "required": True
            },
            {
                "name": "depth",
                "datatype": 0,
                "value": 0.0,
                "displayname": "Ocean Depth",
                "required": True
            }]

        #writeToLog("init: the StdZ value is: {0}\n".format(self.depthval))

    def getconfiguration(self, **scalars):
        configuration = {
          "referenceproperties": (4, 8)
        }

        return configuration

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["bandcount"] = 1
        kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0.0, "maximum": 1.0},)
        self.depthval = abs(float(kwargs["depth"]))

        #writeToLog("bind: the StdZ value is: {0}\n".format(self.depthval))
        return kwargs

    def read(self, **kwargs):
        temperatureblock = kwargs["temperature_pixelblock"]
        salinityblock = kwargs["salinity_pixelblock"]

        t_pb = np.array(temperatureblock, dtype="float")
        s_pb = np.array(salinityblock, dtype="float")

        #Temperature(c)
        tmina = 17.99
        tminp = 26.37
        tmaxp = 29.15
        tmaxa = 33.35

        np.putmask(t_pb, t_pb <= tminp, (t_pb - tmina) / (tminp - tmina))
        np.putmask(t_pb, t_pb >= tmaxp, (t_pb - tmaxa) / (tmaxp - tmaxa))
        np.putmask(t_pb, (t_pb > tminp) & (t_pb < tmaxp), 1)
        np.putmask(t_pb, t_pb < 0, 0)

        #Salinity(psu)
        smina = 28.81
        sminp = 32.27
        smaxp = 35.81
        smaxa = 36.79

        np.putmask(s_pb, s_pb <= sminp, (s_pb - smina) / (sminp - smina))
        np.putmask(s_pb, s_pb >= smaxp, (s_pb - smaxa) / (smaxp - smaxa))
        np.putmask(s_pb, (s_pb > sminp) & (s_pb < smaxp), 1)
        np.putmask(s_pb, s_pb < 0, 0)

        #writeToLog("read: the StdZ value is: {0}\n".format(self.depthval))
        suitd = 0
        #Depth (meter)
        dmina = 0
        dminp = 2
        dmaxp = 11
        dmaxa = 20
        if self.depthval <= 2:
            if self.depthval < 0:
                suitd = 0
            else:
                suitd = (self.depthval - dmina) / (dminp - dmina)
        elif self.depthval >= 11:
            if self.depthval > 20:
                suitd = 0
            else:
                suitd = (self.depthval - dmaxa) / (dmaxp - dmaxa)
        else:
            suitd = 1

        #Get overall probability by timing all conditions
        out_pb = (t_pb * s_pb) * suitd

        np.copyto(kwargs["output_pixelblock"], out_pb, casting="unsafe")
        return kwargs

    def getproperty(self, name, defaultvalue, **kwargs):
        if name.lower == "variable":
            return "FishHabitatSuitabilityDepth"
        else:
            return defaultvalue

    def getallproperties(self, **args):
        args["variable"] = "FishHabitatSuitabilityDepth"
        return args

# def writeToLog(message):
#     logpath = r"C:\temp\PAF\pafdebug.log"
#     try:
#         fileobj = open(logpath, "a")
#         fileobj.writelines(message)
#         fileobj.flush()
#         fileobj.close()
#     except Exception:
#         return