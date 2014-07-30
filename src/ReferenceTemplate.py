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



### This class serves as a quick reference to methods and properties associated with a python raster function. 
### As a raster function it doesn't do anything useful. 
### Feel free to use this template a starting point for your implementations or as a cheat-sheet. 

class ReferenceTemplate():
    def __init__(self):
        self.name = "Reference Template Function"
        self.description = "Reference Template Function"

        self.argumentinfo = [
            {
                "name": "some_numeric_argument",
                "datatype": 0,
                "value": 100,
                "displayname": "Friendly Name A",
                "description": "Description of some_numeric_argument",
                "required": True                        # True or False
            },
            {
                "name": "some_text_argument",
                "datatype": 1,
                "value": "default_value",
                "displayname": "Friendly Name B",
                "description": "Description of some_text_argument",
                "required": True
            },
            {
                "name": "raster_argument",
                "datatype": 2,
                "value": "",
                "displayname": "Friendly Name C",
                "description": "Description of raster_argument",
                "required": True
            },
            {
                "name": "raster_collection_argument",
                "datatype": 3,
                "value": "",
                "displayname": "Friendly Name D",
                "description": "Description of raster_collection_argument",
                "required": True
            },
        ]

    def getconfiguration(self, **scalars):
        # scalars
        return {
          "extractbandids": (scalars["red"], scalars["ir"]),        # extract only the two bands corresponding to user-specified red and infrared band indexes.
          "compositerasters": False,                                # input is a single raster, band compositing doesn't apply.
          "referenceproperties": 2 | 4                              # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def bind(self, **kwargs):
        kwargs["output_rasterinfo"]["bandcount"] = 1            # output is a single band raster
        kwargs["output_rasterinfo"]["pixeltype"] = "32_BIT_FLOAT"   # ... with floating-point pixel values.
        kwargs["output_rasterinfo"]["statistics"] = ({"minimum": 0.0, "maximum": 200.0}, )  # we know a little about the stats of the outgoing raster (scaled NDVI). 

        #"rasterattributetable"         // Tuple(String + Tuple(Strings : Tuple containing path to the attribute table and field names.
        #"bandcount"                    // Int
        #"blockheight"                  // Int
        #"blockwidth"                   // Int
        #"cellsize"                     // Tuple(Floats) : Tuple of x- and y-cell-size values.
        #"colormap"                      // [Tuple(3 * numpy.ndarray)] : Tuple of three floating-point arrays corresponding to values for Red, Green, and Blue channel.
        #"extent"                       // Tuple(Floats) : Tuple of XMin, YMin, XMax, YMax values.
        #"firstpyramidlevel"            // Int: 
        #"format"                       // String: 
        #"geodataxform"                 // String: XML-string representation of the associated XForm.
        #"histogram"                    // Tuple(numpy.ndarrays): Tuple of histogram values. Each value is a numpy array of histogram values for each band.
        #"levelofdetails"               // Int: The number of level of details in the input raster.
        #"maximumcellsize"              // Tuple(Floats): Tuple of x and y cell size values.
        #"maxpyramidlevel"              // Int
        #"nativeextent"                 // Tuple(Floats): Tuple of XMin, YMin, XMax, YMax values.
        #"nativespatialreference"       // Int: EPSG code for the spatial reference.
        #"nodata"                       // Float
        #"origin"                       // Tuple(Floats): Tuple of (x,y) coordinate corresponding to the origin. 
        #"pixeltype"                    // String: String representation of pixel type of the input raster.
        #"resampling"                   // Bool
        #"spatialreference"             // Int: EPSG code for the spatial reference.
        #"bandselection"                // Bool
        #"statistics"                   // Tuple(Dicts): Tuple of statistics values. Each vale is a dictionary contains the following attributes for each band. 
        #"minimum"                      // Float
        #"maximum"                      // Float
        #"mean"                         // Float
        #"standarddeviation"            // Float
        #"skipfactorx"                  // Int
        #"skipfactory"                  // Int


        return kwargs

    def read(self, **kwargs):
        inblock = kwargs["raster_pixelblock"]                   # get the input raster pixel block.
        red = np.array(inblock[0], dtype="float")               # extractbandids ensures first band is Red.
        ir = np.array(inblock[1], dtype="float")                # extractbandids ensures second band is Infrared.

        np.seterr(divide="ignore")

        outblock = np.multiply(np.divide((ir - red), (ir + red, 100.0) + 100.0        # scale and offset the NDVI value (ir-red)/(ir+red).
        np.copyto(kwargs["output_pixelblock"], outblock, casting="unsafe")              # copy local array to output pixel block.
        return kwargs

    def getproperty(self, name, defaultvalue, **kwargs):
        if name.lower == "datatype":
            return "Processed"
        else:
            return defaultvalue

    def getallproperties(self, **args):
        args["datatype"] = "Processed"                          # outgoing raster is now 'Processed'.
        args["cloudcover"] = 50.0
        return args

    def getbandproperty(self, name, bandindex, defaultvalue, **kwargs):
        return defaultvalue

    def getallbandproperties(self, bandindex, **args):
        return args
