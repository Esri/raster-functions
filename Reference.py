import numpy as np


### This class serves as a quick reference for all methods and attributes associated with a python raster function. 
### It doesn't performs any processing. 
### Feel free to use this template a starting point for your implementation or as a cheat-sheet. 

class ReferenceFunction():                                      
    ## Class name defaults to module name unless specified in the Python Adapter function property page

    def __init__(self):                                         # Intialize your class' attributes here.
        self.name = "Reference Function"                            #... this is a short name for the function. Traditionally named "<something> Function".
        self.description = "This is a template function."           #... a detailed description of what this function does. 

    def getParameterInfo(self):                                 # This method returns information on each parameter to your function as a list of dictionaries. 
        # This method must be defined.
        
        return [                                                    #... each entry in the list corresponds to an input parameter
            {                                                       #... the dictionary contains attributes that further describe aspects of a parameter
                'name': 'keyword',                                  #... the keyword associated with this parameter that enables dictionary lookup in other methods
                'dataType': 0,                                      #... the data type of the value held by this parameter Allowed values: {0: numeric, 1: string, 2: raster, 3: rasters, 4: boolean}
                'value': None,                                      #... the default value associated with this parameter
                'displayName': "Friendly Name",                     #... a friendly name that represents this parameter in Python Adapter function's property page and other UI components
                'domain': ('Value 1', 'Value 2', 'Value 3'),        #... Indicates the set of allowed values for this parameter. If specified, the property page shows a drop-down list pre-populated with these values. This attribute is applicable only to string parameters (dataType: 1).
                'description': "Description of this argument",      #... a detailed description of this parameter primarily displayed as tooltip in Python Adapter function's property page.
                'required': True                                    #... indicates whether this parameter is required or optional. Allowed values: {True, False}.
            },

            # ... add dictionaries here for additional arguments
        ]

    def getConfiguration(self, **scalars):                      # This method can override aspects of function raster dataset based on all scalar (non-raster) user inputs.
        # This method, if defined, gets called after .getParameterInfo() but before .updateRasterInfo(). 
        # Use scalar['keyword'] to obtain the user-specified value of the scalar whose 'name' attribute is 'keyword' in the .getParameterInfo().

        return {
          'extractBands': (),                                       # 
          'compositeRasters': False,                                # 
          'referenceProperties': 1 | 2 | 4,                         # 
          'invalidateProperties': 2 | 4                             # 
        }

    def updateRasterInfo(self, **kwargs):                       # This method can update the output raster's information
        # This method, if defined, gets called after .getConfiguration() and is invoked each time a function raster dataset containing this python function is initialized. 
        # kwargs contains all user-specified scalar values and information associated with all input rasters.
        # Use kwargs['keyword'] to obtain the user-specified value of the scalar whose 'name' attribute is 'keyword' in the .getParameterInfo().
        # If 'keyword' represents a raster, kwargs['keyword_info'] will be a dictionary representing the the information associated with the raster. 
        # kwargs['output_info'] is always available and populated with values based on the first raster parameter and .getConfiguration().
        # This method can update the values of the dictionary in kwargs['output_info'] based on the operation in .updatePixels() 

        # Access aspects of a particular raster's information like this: kwargs['<rasterName>_info']['<propertyName>']
        #... where <rasterName> corresponds to a raster parameter xxx
        #... and <propertyName> is an aspect of the raster information and one of the following.
        
        # rasterAttributeTable    : Tuple(String + Tuple(Strings)) : Tuple containing path to the attribute table and field names.
        # bandCount               : Int
        # blockHeight             : Int
        # blockWidth              : Int
        # cellSize                : Tuple(Floats) : Tuple of x- and y-cell-size values.
        #                         : 
        # colormap                : Tuple(ndarray(int32), ndarray(uint8), ndarray(uint8), ndarray(uint8)) : A tuple of four arrays where the first array contains 32-bit integers corresponding to pixel values in the indexed raster. 
        #                         : The subsequent three arrays contain unsigned 8-bit integers corresponding to the Red, Green, and Blue components of the mapped color. The sizes of all arrays must match and corresponds to the number of colors in the RGB image. 
        #                         : 
        # extent                  : Tuple(Floats) : Tuple of XMin, YMin, XMax, YMax values.
        # firstPyramidLevel       : Int: 
        # format                  : String: 
        # geodataXform            : String: XML-string representation of the associated XForm.
        # histogram               : Tuple(numpy.ndarrays): Tuple of histogram values. Each value is a numpy array of histogram values for each band.
        # levelOfDetails          : Int: The number of level of details in the input raster.
        # maximumCellSize         : Tuple(Floats): Tuple of x and y cell size values.
        # maxPyramidLevel         : Int
        # nativeExtent            : Tuple(Floats): Tuple of XMin, YMin, XMax, YMax values.
        # nativeSpatialReference  : Int: EPSG code for the spatial reference.
        # noData                  : Float
        # origin                  : Tuple(Floats): Tuple of (x,y) coordinate corresponding to the origin. 
        # pixelType               : String: String representation of pixel type of the input raster.
        # resampling              : Bool
        # spatialReference        : Int: EPSG code for the spatial reference.
        # bandSelection           : Bool
        # statistics              : Tuple(Dicts): Tuple of statistics values. Each vale is a dictionary contains the following attributes for each band. 
        #   minimum                 : Float
        #   maximum                 : Float
        #   mean                    : Float
        #   standardDeviation       : Float
        #   skipFactorX             : Int
        #   skipFactorY             : Int

        # Note:
        #... The tuple passed in by CellSize and MaximumCellSize attributes can be used in the arcpy.Point() to create a python point object.
        #... The tuple passed in by Extent, NativeExtent and Origin attributes can be used in the arcpy.Extent() to create a python extent object.
        #... The epsg code passed in by NativeSpatialReference and SpatialReference attribute can be used in arcpy.SpatialReference() to create a python spatial refrence object.
        #... The tuple passed in by RasterAttributeTable attribute can be used in the arcpy.da.TableToNumPyArray() to access the data. The values should be stored back at the path passed in as first argument in the tuple.

        kwargs['output_info']['bandCount'] = 1                # output is a single band raster
        kwargs['output_info']['pixelType'] = '32_BIT_FLOAT'   # ... with floating-point pixel values.
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 200.0}, )   
        return kwargs

    def updatePixels(self, **pixelBlocks):                      # This method can update output pixels based on pixel blocks associated with all input rasters.
        # 
        # The pixelBlocks dictionary does not contain scalars. 
        inputBlock = pixelBlocks['raster_pixels']                  # get the input raster pixel block.
        inputBlocks = pixelBlocks['rasters_pixels']                  # get the input raster pixel block.
        red = np.array(inblock[0], dtype='float')                   # extractbandids ensures first band is Red.
        ir = np.array(inblock[1], dtype='float')                    # extractbandids ensures second band is Infrared.

        np.copyto(pixelBlocks['output_pixels'], outblock, casting='unsafe')              # copy local array to output pixel block.
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):   # This method can update dataset-level or band-level key metadata.
        # bandIndex == -1 indicates that dataset-level key properties are being requested.

        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'               # outgoing raster is now 'Processed'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'NDVI'
        return keyMetadata
