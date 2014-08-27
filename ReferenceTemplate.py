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

class ReferenceFunction():                                                  # Class name defaults to module name unless specified in the Python Adapter Function property page
    def __init__(self):                                                     # Intialize your class' attributes here.
        self.name = "Reference"                                             # ... this is a short name for the function. Traditionally named "<something> Function".
        self.description = "Reference Function"                             # ... a friendly detailed description of what this function does. 

    def getParameterInfo(self):                                             # Return information on each parameter to your function here as a list of dictionaries. 
        return [                                                            # ...each entry in the list corresponds to an input parameter
            {                                                               # ...the dictionary contains attributes that further describe aspects of a parameter
                "name": "some_numeric_argument",                            # ...the name 
                "dataType": 0,
                "value": 100,
                "displayName": "Friendly Name A",
                "description": "Description of some_numeric_argument",
                "required": True                        # True or False
            },
            {
                "name": "some_text_argument",
                "dataType": 1,
                "value": "default_value",
                "displayName": "Friendly Name B",
                "description": "Description of some_text_argument",
                "required": True
            },
            {
                "name": "raster_argument",
                "dataType": 2,
                "value": "",
                "displayName": "Friendly Name C",
                "description": "Description of raster_argument",
                "required": True
            },
            {
                "name": "raster_collection_argument",
                "dataType": 3,
                "value": "",
                "displayName": "Friendly Name D",
                "description": "Description of raster_collection_argument",
                "required": True
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          "extractBands": (scalars["red"], scalars["ir"]),        # extract only the two bands corresponding to user-specified red and infrared band indexes.
          "compositeRasters": False,                                # input is a single raster, band compositing doesn't apply.
          "referenceProperties": 2 | 4,                              # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
          "invalidateProperties": 2 | 4                              # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }

    def updateRasterInfo(self, **kwargs):
        kwargs["output_rasterInfo"]["bandCount"] = 1            # output is a single band raster
        kwargs["output_rasterInfo"]["pixelType"] = "32_BIT_FLOAT"   # ... with floating-point pixel values.
        kwargs["output_rasterInfo"]["statistics"] = ({"minimum": 0.0, "maximum": 200.0}, )  # we know a little about the stats of the outgoing raster (scaled NDVI). 

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

    def updatePixels(self, **pixelBlocks):
        inblock = pixelBlocks["raster_pixelBlock"]                   # get the input raster pixel block.
        red = np.array(inblock[0], dtype="float")               # extractbandids ensures first band is Red.
        ir = np.array(inblock[1], dtype="float")                # extractbandids ensures second band is Infrared.

        np.seterr(divide="ignore")

        outblock = np.multiply(np.divide(ir - red, ir + red), 100.0) + 100.0            # scale and offset the NDVI value (ir-red)/(ir+red).
        np.copyto(pixelBlocks["output_pixelBlock"], outblock, casting="unsafe")              # copy local array to output pixel block.
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata["datatype"] = "Processed"               # outgoing raster is now 'Processed'
        elif bandIndex == 0:
            keyMetadata["wavelengthmin"] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata["wavelengthmax"] = None
            keyMetadata["bandname"] = "NDVI"
        return keyMetadata
