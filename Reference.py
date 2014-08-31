import numpy as np


"""
    This class serves as a quick reference for all methods and attributes associated with a python raster function. 
    Feel free to use this template a starting point for your implementation or as a cheat-sheet. 
"""

class Reference():
    """Class name defaults to module name unless specified in the Python Adapter function's property page.

    """


    def __init__(self): 
        """Initialize your class' attributes here.

        """
        self.name = "Reference Function"                # a short name for the function. Usually named "<something> Function".
        self.description = "Story of the function..."   # a detailed description of what this function does. 


    def isLicensed(self): 
        """This method, if defined, indicates whether this python raster function is licensed to execute. 
        
        Args:
            None

        Returns:
            True if it's OK to execute.
        """
        return True


    def getParameterInfo(self): 
        """This method returns information on each parameter to your function as a list of dictionaries. 

        This method must be defined.

        Args:
            None

        Returns:
            A list of dictionaries where each entry in the list corresponds to an input parameter--and describes the parameter.
            These are the recognized attributes of a parameter: 
            . name :        The keyword associated with this parameter that enables dictionary lookup in other methods
            . dataType :    The data type of the value held by this parameter.
                            Allowed values: {'numeric', 'string', 'raster', 'rasters', 'boolean'}
            . value :       The default value associated with this parameter.
            . required :    Indicates whether this parameter is required or optional. Allowed values: {True, False}.
            . displayName : A friendly name that represents this parameter in Python Adapter function's property page and other UI components
            . domain :      Indicates the set of allowed values for this parameter. 
                            If specified, the property page shows a drop-down list pre-populated with these values. 
                            This attribute is applicable only to string parameters (dataType='string').
            . description : Details on this parameter that's displayed as tooltip in Python Adapter function's property page.
        """    
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The story of this raster...",      
            },
            {
                'name': 'processing_parameter',
                'dataType': 'numeric',
                'value': "<default value>",
                'required': False,
                'domain': ('Value 1', 'Value 2'),
                'displayName': "Friendly Name",
                'description': "The story of this parameter...",
            },

            # ... add dictionaries here for additional parameters
        ]


    def getConfiguration(self, **scalars):
        """This method can manage how the output raster is pre-constructed gets.

        This method, if defined, controls aspects of parent dataset based on all scalar (non-raster) user inputs.
        It's invoked after .getParameterInfo() but before .updateRasterInfo(). 

        Args:
            Use scalar['x'] to obtain the user-specified value of the scalar whose 'name' attribute is 
            'x' in the .getParameterInfo().

        Returns:
            A dictionary describing the configuration. These are the recognized configuration attributes:

            . extractBands :         Tuple(ints) containing indexes of bands of the input raster that need to be extracted. 
                                     The first band has index 0. 
                                     If unspecified, all bands of the input raster are available in .updatePixels()
            . compositeRasters :     Boolean indicating whether all input rasters are composited as a single multi-band raster. 
                                     Defaults to False. If set to True, a raster by the name 'compositeraster' is available 
                                     in .updateRasterInfo() and .updatePixels().
            . inheritProperties :    Bitwise-OR'd integer that indicates the set of input raster properties that are inherited 
                                     by the output raster. If unspecified, all properties are inherited. 
                                     These are the recognized values:
                                     . 1 : Pixel type
                                     . 2 : NoData
                                     . 4 : Dimensions (spatial reference, extent, and cell-size)
                                     . 8 : Resampling type
            . invalidateProperties : Bitwise-OR'd integer that indicates the set of properties of the parent dataset that needs 
                                     to be invalidated. If unspecified, no property gets invalidated.
                                     These are the recognized values:
                                     . 1 : XForm stored by the function raster dataset.
                                     . 2 : Statistics stored by the function raster dataset.
                                     . 4 : Histogram stored by the function raster dataset.
                                     . 8 : The key properties stored by the function raster dataset.
            . padding :              The number of extra pixels needed on each side of input pixel blocks.
            . inputMask :            Boolean indicating whether NoData mask arrays associated with all input rasters are needed
                                     by this function for proper construction of output pixels and mask. 
                                     If set to True, the input masks are made available in the pixelBlocks keyword 
                                     argument in .updatePixels(). If unspecified, input masks are not made available--
                                     in the interest of performance. 
        """
        return {
          'extractBands': (0, 2),            # we only need the first (red) and third (blue) band.
          'compositeRasters': False,
          'inheritProperties': 2 | 4 | 8,    # inherit everything but the pixel type (1)
          'invalidateProperties': 2 | 4 | 8, # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                      # No padding needed. Return input pixel block as is. 
          'inputMask': False                 #  
        }


    def updateRasterInfo(self, **kwargs):
        """This method can update the output raster's information.

        This method, if defined, gets called after .getConfiguration().
        It's invoked each time a function raster dataset containing this python function is initialized. 

        Args:
            kwargs contains all user-specified scalar values and information associated with all input rasters.
            Use kwargs['x'] to obtain the user-specified value of the scalar whose 'name' attribute is 'x' in the .getParameterInfo().
        
            If 'x' represents a raster, kwargs['x_info'] will be a dictionary representing the the information associated with the raster. 
            Access aspects of a particular raster's information like this: kwargs['<rasterName>_info']['<propertyName>']
            where <rasterName> corresponds to a raster parameter where 'rasterName' is the value of the 'name' attribute of the parameter.
            and <propertyName> is an aspect of the raster information.

            If <rasterName> represents a parameter of type rasters (dataType='rasters'), then 
            kwargs['<rasterName>_info'] is a tuple of raster info dictionaries.

            kwargs['output_info'] is always available and populated with values based on the first raster parameter and .getConfiguration().

            These are the properties associated with a raster information:
            . bandCount :             Integer representing the number of bands in the raster. 
            . pixelType :             String representation of pixel type of the raster. These are the allowed values:
                                      {'t1', 't2', 't4', 'i1', 'i2', 'i4', 'u1', 'u2', 'u4', 'f4', 'f8'}
                                      cf: http://docs.scipy.org/doc/numpy/reference/arrays.interface.html
            . noData :                TODO.
            . cellSize :              Tuple(2 x floats) representing cell-size in the x- and y-direction.
            . nativeExtent :          Tuple(4 x floats) representing XMin, YMin, XMax, YMax values of the native image coordinates.
            . nativeSpatialReference: Int representing the EPSG code of the native image coordinate system.
            . geodataXform :          XML-string representation of the associated XForm between native image and map coordinate systems.
            . extent :                Tuple(4 x floats) representing XMin, YMin, XMax, YMax values of the map coordinates.
            . spatialReference :      Int representing the EPSG code of the raster's map coordinate system.
            . colormap:               Tuple(ndarray(int32), 3 x ndarray(uint8)) A tuple of four arrays where the first array contains 32-bit integers 
                                      corresponding to pixel values in the indexed raster. The subsequent three arrays contain unsigned 8-bit integers 
                                      corresponding to the Red, Green, and Blue components of the mapped color. The sizes of all arrays 
                                      must match and correspond to the number of colors in the RGB image. 
            . rasterAttributeTable :  Tuple(String, Tuple(Strings)) : A tuple of a string representing the path of the attribute table, 
                                      and another tuple representing field names.
                                      Use the information in this tuple with arcpy.da.TableToNumPyArray() to access the values.
            . levelOfDetails :        Int: The number of level of details in the input raster.
            . origin :                Tuple(Floats): Tuple of (x,y) coordinate corresponding to the origin. 
            . resampling :            Boolean
            . bandSelection :         Boolean
            . histogram :             Tuple(numpy.ndarrays): Tuple where each entry is an array of histogram values of a band.
            . statistics :            Tuple(dicts): Tuple of statistics values. 
                                      Each entry in the tuple is a dictionary containing the following attributes of band statistics:
                                      . minimum : Float. Approximate lowest value.
                                      . maximum : Float. Approximate highest value.
                                      . mean : Float. Approximate average value.
                                      . standardDeviation : Float. Approximate measure of spread of values about the mean. 
                                      . skipFactorX : Int. Number of horizontal pixels between samples when calculating statistics.
                                      . skipFactorY : Int. Number of vertical pixels between samples when calculating statistics.
                              
        Returns:
            A dictionary containing updated output raster info. 
            This method can update the values of the dictionary in kwargs['output_info'] depending on the kind of 
            operation in .updatePixels() 

        Note:
            . The tuple in cellSize and maximumCellSize attributes can be used to construct an arcpy.Point object.
            . The tuple in extent, nativeExtent and origin attributes can be used to construct an arcpy.Extent object.
            . The epsg code in nativeSpatialReference and spatialReference attributes can be used to construct an 
              arcpy.SpatialReference() object.
        """
        kwargs['output_info']['bandCount'] = 1                  # output is a single band raster
        kwargs['output_info']['pixelType'] = 'f4'               # ... with floating-point pixel values.
        kwargs['output_info']['statistics'] = ()                # invalidate any statistics
        kwargs['output_info']['histogram'] = ()                 # invalidate any histogram
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        """This method can provide output pixels based on pixel blocks associated with all input rasters.

        A python raster function that doesn't actively modify output pixel values doesn't need to define this method. 

        Args:
            . tlc : Tuple(2 x floats) representing the coordinates of the top-left corner of the pixel request.
            . shape : Tuple(ints) representing the shape of ndarray that defines the output pixel block. 
                For a single-band pixel block, the tuple contains two ints (rows, columns). 
                For multi-band output raster, the tuple defines a three-dimensional array (bands, rows, columns).
                The shape associated with the output pixel block must match this arguments value.
            . props : A dictionary containing properties that define the virtual output raster from which 
                a pixel block--of size and location is defined by 'shape' and 'tlc' arguments--is being requested.
                These are the available attributes in this dictionary:
                . extent : Tuple(4 x floats) representing XMin, YMin, XMax, YMax values of the output 
                           raster's map coordinates.
                . pixelType : String representation of pixel type of the raster. These are the allowed values:
                              {'t1', 't2', 't4', 'i1', 'i2', 'i4', 'u1', 'u2', 'u4', 'f4', 'f8'}
                              cf: http://docs.scipy.org/doc/numpy/reference/arrays.interface.html
                . spatialReference : Int representing the EPSG code of the output raster's map coordinate system.
                . cellSize : Tuple(2 x floats) representing cell-size in the x- and y-direction.                
                . width : Number of columns of pixels in the output raster.
                . height : Number of rows of pixels in the output raster.
                . noData : TODO.
            . pixelBlocks : Keyword argument containing pixels and mask associated with each input raster.
                            
            For a raster parameter with dataType='raster' and name='x', pixelBlocks['x_pixels'] and 
            pixelBlocks['x_mask'] are numpy.ndarrays of pixel and mask values for that input raster. 
            For a parameter of type rasters (dataType='rasters'), these are tuples of ndarrays--one entry per raster.
            The arrays are three-dimensional for multiband rasters. 

            Note:
            . The pixelBlocks dictionary does not contain any scalars parameters.

        Returns:
            A dictionary with a numpy array containing pixel values in the 'output_pixels' key and, 
            optionally, an array representing the mask in the 'output_mask' key.

            The 'shape' argument defines the shape of the ndarray in 'output_pixels'. It's two- or three-
            dimensional depending on whether it's a single- or multi-band output raster pixel block.
             
            If a mask is returned, the shape of the ndarray in 'output_mask' is defined by the last two values 
            of the 'shape' tuple. Mask is always two-dimensional.

        References:
            
        """
        if not pixelBlocks.has_key("raster_pixels"):
          raise Exception("No input raster was provided.")

        inputBlock = pixelBlocks['raster_pixels']           # get pixels of an raster
        red  = np.array(inputBlock[0], 'f4')                # assuming red's the first band 
        blue = np.array(inputBlock[1], 'f4')                # assuming blue's the second band... per extractBands in .getConfiguration() 
        outBlock = (red + blue) / 2.0                       # this is just an example. nothing complicated here. 

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        """This method can update dataset-level or band-level key metadata.

        When a request for a dataset's key metadata is made, this method (if present) allows the python raster function 
        to invalidate or overwrite specific requests. 

        Args:
            . names :       A tuple containing names of the properties being requested. 
                            An empty tuple indicates that all properties are being requested. 
            . bandIndex:    A zero-based integer representing the raster band for which key metadata is being requested. 
                            bandIndex == -1 indicates that the request is for dataset-level key properties.
            . keyMetadata : Keyword argument containing all currently known metadata (or a subset as defined by the names tuple). 
        
        Returns:
            The updated keyMetadata dictionary.
        """
        if bandIndex == -1:                             # dataset-level properties           
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Red_and_Blue'    # ... or something meaningful
        return keyMetadata
