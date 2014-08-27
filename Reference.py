import numpy as np


### This class serves as a quick reference for all methods and attributes associated with a python raster function. 
### Feel free to use this template a starting point for your implementation or as a cheat-sheet. 

class Reference():
    ## Class name defaults to module name unless specified in the Python Adapter function property page

    def __init__(self):     # Initialize your class' attributes here.
        self.name = "Reference Function"                # a short name for the function. Traditionally named "<something> Function".
        self.description = "Story of the function..."   # a detailed description of what this function does. 

    def getParameterInfo(self):     # This method returns information on each parameter to your function as a list of dictionaries. 
        # This method must be defined.
        # Each entry in the list is a dictionary that corresponds to an input parameter--and describes the parameter.
        # These are the recognized attributes of a parameter: 
        #   name :        The keyword associated with this parameter that enables dictionary lookup in other methods
        #   dataType :    The data type of the value held by this parameter.
        #                 Allowed values: {0: numeric, 1: string, 2: raster, 3: rasters, 4: boolean}
        #   value :       The default value associated with this parameter.
        #   required :    Indicates whether this parameter is required or optional. Allowed values: {True, False}.
        #   displayName : A friendly name that represents this parameter in Python Adapter function's property page and other UI components
        #   domain :      Indicates the set of allowed values for this parameter. 
        #                 If specified, the property page shows a drop-down list pre-populated with these values. 
        #                 This attribute is applicable only to string parameters (dataType: 1).
        #   description : A detailed description of this parameter primarily displayed as tooltip in Python Adapter function's property page.
        
        return [
            {
                'name': 'raster',
                'dataType': 2,
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The story of this raster...",      
            },
            {
                'name': 'processing_parameter',
                'dataType': 0,
                'value': "<default value>",
                'required': False,
                'displayName': "Friendly Name",
                'domain': ('Value 1', 'Value 2'),
                'description': "The story of this parameter...",
            },

            # ... add dictionaries here for additional parameters
        ]

    def getConfiguration(self, **scalars):      # This method can manage how the output raster is pre-constructed gets.
        # This method, if defined, controls aspects of parent dataset based on all scalar (non-raster) user inputs.
        # It's invoked after .getParameterInfo() but before .updateRasterInfo(). 
        # Use scalar['keyword'] to obtain the user-specified value of the scalar whose 'name' attribute is 'keyword' in the .getParameterInfo().

        # These are the recognized configuration attributes:
        # . extractBands : Tuple(ints) representing the bands of the input raster that need to be extracted
        # . compositeRasters : Boolean indicating whether all input rasters are composited as a single multi-band raster. 
        # . referenceProperties : Bitwise-OR'd integer that indicates the set of input raster properties that are inherited by the output raster.
        #       1 : Pixel type
        #       2 : NoData
        #       4 : Dimensions (spatial reference, extent, and cellsize)
        #       8 : Resampling type
        #       16: Band ID
        # . invalidateProperties : Bitwise-OR'd integer that indicates the set of properties of the parent dataset that needs to be invalidated. 
        #       1 : XForm stored by the function raster dataset.
        #       2 : Statistics stored by the function raster dataset.
        #       4 : Histogram stored by the function raster dataset.
        #       8 : The key properties stored by the function raster dataset.

        return {
          'extractBands': (0, 2),       # we only need the first (red) and third (blue) band.
          'compositeRasters': False,
          'referenceProperties': 2 | 4 | 8, # inherit everything but the pixel type (1) and band IDs (16) 
          'invalidateProperties': 2 | 4 | 8 # invalidate these aspects because we are modifying pixel values and updating key properties.
        }

    def updateRasterInfo(self, **kwargs):       # This method can update the output raster's information
        # This method, if defined, gets called after .getConfiguration().
        # It's invoked each time a function raster dataset containing this python function is initialized. 

        # kwargs contains all user-specified scalar values and information associated with all input rasters.
        # Use kwargs['keyword'] to obtain the user-specified value of the scalar whose 'name' attribute is 'keyword' in the .getParameterInfo().
        
        # If 'keyword' represents a raster, kwargs['keyword_info'] will be a dictionary representing the the information associated with the raster. 
        # Access aspects of a particular raster's information like this: kwargs['<rasterName>_info']['<propertyName>']
        # where <rasterName> corresponds to a raster parameter where 'rasterName' is the value of the 'name' attribute of the parameter.
        # and <propertyName> is an aspect of the raster information.

        # If <rasterName> represents a parameter of type rasters (dataType: 3), then kwargs['<rasterName>_info'] is a tuple of raster info dictionaries.

        # kwargs['output_info'] is always available and populated with values based on the first raster parameter and .getConfiguration().
        # This method can update the values of the dictionary in kwargs['output_info'] based on the operation in .updatePixels() 

        # These are the properties associated with a raster information:
        #   bandCount :             Integer representing the number of bands in the raster. 
        #   pixelType :             String representation of pixel type of the raster. These are the allowed values:
        #                           {'8_BIT_UNSIGNED', '8_BIT_SIGNED', '16_BIT_UNSIGNED', '16_BIT_SIGNED', '32_BIT_UNSIGNED', '32_BIT_SIGNED', 
        #                            '32_BIT_FLOAT', '1_BIT', '2_BIT', '4_BIT', '64_BIT'}
        #   noData :                Float.
        #   cellSize :              Tuple(2 x floats) representing x- and y-cell-size values.
        #   nativeExtent :          Tuple(4 x floats) representing XMin, YMin, XMax, YMax values of the native image coordinates.
        #   nativeSpatialReference: Int representing the EPSG code of the native image coordinate system.
        #   geodataXform :          XML-string representation of the associated XForm between native image and map coordinate systems.
        #   extent :                Tuple(4 x floats) representing XMin, YMin, XMax, YMax values of the map coordinates.
        #   spatialReference :      Int representing the EPSG code of the raster's map coordinate system.
        #   colormap:               Tuple(ndarray(int32), 3 x ndarray(uint8)) A tuple of four arrays where the first array contains 32-bit integers 
        #                           corresponding to pixel values in the indexed raster. The subsequent three arrays contain unsigned 8-bit integers 
        #                           corresponding to the Red, Green, and Blue components of the mapped color. The sizes of all arrays 
        #                           must match and correspond to the number of colors in the RGB image. 
        #   rasterAttributeTable :  Tuple(String, Tuple(Strings)) : A tuple of a string representing the path of the attribute table, 
        #                           and another tuple representing field names.
        #                           Use the information in this tuple with arcpy.da.TableToNumPyArray() to access the values.
        #   levelOfDetails :        Int: The number of level of details in the input raster.
        #   origin :                Tuple(Floats): Tuple of (x,y) coordinate corresponding to the origin. 
        #   resampling :            Bool
        #   bandSelection :         Bool
        #   histogram :             Tuple(numpy.ndarrays): Tuple where each entry is an array of histogram values of a band.
        #   statistics :            Tuple(dicts): Tuple of statistics values. 
        #                           Each entry in the tuple is a dictionary containing the following attributes of band statistics:
        #                           . minimum : Float. Approximate lowest value.
        #                           . maximum : Float. Approximate highest value.
        #                           . mean : Float. Approximate average value.
        #                           . standardDeviation : Float. Approximate measure of spread of values about the mean. 
        #                           . skipFactorX : Int. Number of horizontal pixels between samples when calculating statistics.
        #                           . skipFactorY : Int. Number of vertical pixels between samples when calculating statistics.

        # Note:
        # . The tuple in cellSize and maximumCellSize attributes can be used to construct an arcpy.Point object.
        # . The tuple in extent, nativeExtent and origin attributes can be used to construct an arcpy.Extent object.
        # . The epsg code in nativeSpatialReference and spatialReference attributes can be used to construct an arcpy.SpatialReference() object.

        kwargs['output_info']['bandCount'] = 1                # output is a single band raster
        kwargs['output_info']['pixelType'] = '32_BIT_FLOAT'   # ... with floating-point pixel values.
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 200.0}, )   
        return kwargs

    def updatePixels(self, **pixelBlocks):      # This method can provide output pixels based on pixel blocks associated with all input rasters.
        # A python raster function that doesnt actively modify out pixel values doesn't need to define this method. 

        # The pixelBlock keyword argument contains pixels and mask associated with each input raster.
        # If 'keyword' represents a parameter of type raster, pixelBlocks['keyword_pixels'] and pixelBlocks['keyword_mask'] are 
        # numpy.ndarrays of pixel and mask values. If 'keyword' represents a parameter of type rasters, these are tuples of ndarrays.
        # The arrays are three-dimensional for multiband rasters. 
        
        # This method can update pixelBlocks['output_pixels'] and pixelBlocks['output_mask']. 
        # Note: the pixelBlocks dictionary does not contain any scalars parameters.

        if not pixelBlocks.has_key("raster_pixels"):
          raise Exception("No input raster was provided.")

        inputBlock = pixelBlocks['raster_pixels']           # get pixels of an raster
        red  = np.array(inputBlock[0], dtype='float')       # assuming red's the first band 
        blue = np.array(inputBlock[1], dtype='float')       # assuming blue's the second band... per extractBands in .getConfiguration() 
        outBlock = (red + blue) / 2.0                       # this is just an example. nothing complicated here. 

        np.copyto(pixelBlocks['output_pixels'], outBlock, casting='unsafe')     # copy local array to output pixel block.
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):       # This method can update dataset-level or band-level key metadata.
        # When a request for a dataset's key metadata is made, this method (if present) allows the python raster function 
        # to invalidate or overwrite specific requests. 

        # The names argument is a tuple of property names being requested. An empty tuple indicates that all properties are being requested. 
        # The bandIndex argument is a integer representing the raster band for which key metadata is being requested. 
        # bandIndex == -1 indicates that the request is for dataset-level key properties.
        # The keyMetadata keyword argument contains all currently known key metadata (or a subset as defined by the names tuple). 
        
        # This method can update the keyMetadata dictionary and must return it. 

        if bandIndex == -1:                             # dataset-level properties           
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Red_and_Blue'    # ... or something meaningful
        return keyMetadata
