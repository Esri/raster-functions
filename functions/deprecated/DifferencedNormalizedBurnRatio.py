import numpy as np


class NBR():
    def __init__(self):
        self.name = "NBR Function"
        self.description = "This function computes Differenced Normalized Burn Ratio (delta NBR) given two raster inputs (a before fire image and a after fire image) and user defined Near Infrared and Short-wave Infrared bands number (e.g. Band 4, 0.76-0.90 microns, in Landsat7 & Band 7, 2.08-2.35 microns, in Landsat7)."
        self.applyScaling = True
        self.applyColormap = False

    # getParameterInfo() describes all raster and scalar inputs to the raster function.
    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Before Fire Image",
                'description': "The 'before' multi-band input raster containing near infrared and short-wave infrared bands."
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "After Fire Image",
                'description': "The 'after' multi-band input raster containing near infrared and short-wave infrared bands."
            },
            {
                'name': 'nir',
                'dataType': 'numeric',
                'value': 1,
                'required': True,
                'displayName': "Near Infrared Band Index",
                'description': "The index of the near infrared band. The first band has index 1."
            },
            {
                'name': 'swir',
                'dataType': 'numeric',
                'value': 2,
                'required': True,
                'displayName': "RShort-wave Infrared Band Index",
                'description': "The index of the short-wave infrared band. The first band has index 1."
            },
            {
                'name': 'method',
                'dataType': 'string',
                'value': 'Colormap',
                'required': False,
                'domain': ('Raw', 'Grayscale', 'Colormap'),
                'displayName': "Output Image Type",
                'description': ("The type of output expected from this function. Specify Raw for scientific analysis. "
                                "Pick Grayscale or Colomap for visualization.")
            },
        ]

    # getConfiguration() helps define attributes that configures how input rasters are read and the output raster constructed.
    def getConfiguration(self, **scalars):
        nir = int(scalars.get('nir', 1))
        swir = int(scalars.get('swir', 2))
        
        return {
          'extractBands': (nir - 1, swir -1),    # extract only the two bands corresponding to user-specified near infrared and shortwave infrared band indexes in all rasters
          'compositeRasters': False,            # input is a single raster, band compositing doesn't apply.
          'inheritProperties': 4 | 8,           # inherit all but the pixel type and NoData from the input raster
          'invalidateProperties': 2 | 4 | 8,    # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values).
          'inputMask': False                    # Don't need input raster mask in .updatePixels().
        }


    # updateRasterInfo() enables you to define the location and dimensions of the output raster.
    def updateRasterInfo(self, **kwargs): #The keyword argument kwargs contains all user-specified scalar values and information associated with each input rasters. 
        method = kwargs.get('method', 'Colormap').lower() #Use kwargs['x'] to obtain the user-specified value of the scalar whose name attribute is x in the .getParameterInfo().
        self.applyColormap = method.lower() == 'colormap'
        self.applyScaling = self.applyColormap or method.lower() == 'grayscale'

        maximumValue = 1.0
        if self.applyScaling:                                   # maximum output value depends on whether we are scaling
            maximumValue = 200.0

        colormap = ()
        pixelType = 'f4' # f Floating point
        if self.applyColormap:
            pixelType = 'u1'
            colormap = (np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255], dtype='int32'),
                        np.array([36, 36, 36, 36, 245, 245, 245, 245, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 247, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 252, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 253, 250, 244, 238, 234, 231, 223, 217, 211, 205, 200, 195, 189, 184, 180, 174, 169, 163, 160, 154, 148, 143, 138, 134, 130, 126, 117, 115, 112, 106, 100, 94, 92, 90, 81, 75, 71, 66, 62, 56, 51, 51, 51, 50, 50, 50, 50, 49, 49, 49, 48, 48, 48, 48, 48, 48, 48, 48, 47, 47, 47, 47, 46, 46, 46, 46, 45, 45, 45, 45, 44, 44, 44, 43, 43, 43, 43, 43, 43, 42, 42, 42, 42, 42, 42, 42, 41, 41, 41, 41, 40, 40, 40, 40, 40, 39, 39, 39, 39, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38], dtype='uint8'),
                        np.array([0, 0, 0, 0, 20, 24, 29, 31, 33, 33, 37, 41, 41, 41, 45, 45, 47, 49, 49, 54, 54, 56, 58, 58, 62, 62, 62, 67, 67, 67, 69, 71, 71, 75, 75, 78, 79, 79, 79, 81, 83, 83, 87, 87, 90, 92, 93, 93, 97, 97, 97, 97, 101, 101, 101, 101, 105, 105, 107, 109, 109, 113, 118, 119, 121, 126, 132, 133, 135, 141, 144, 150, 152, 153, 159, 163, 165, 168, 174, 176, 181, 183, 186, 191, 197, 201, 203, 205, 209, 214, 216, 218, 224, 228, 234, 236, 238, 243, 248, 252, 252, 252, 250, 247, 246, 245, 240, 237, 235, 233, 230, 227, 224, 222, 220, 217, 214, 212, 210, 207, 204, 201, 199, 197, 194, 191, 189, 186, 184, 181, 179, 176, 174, 173, 168, 166, 163, 160, 158, 156, 153, 153, 153, 150, 150, 150, 150, 148, 148, 148, 145, 145, 145, 145, 143, 143, 143, 143, 140, 140, 140, 140, 138, 138, 138, 138, 135, 135, 135, 135, 133, 133, 133, 130, 130, 130, 130, 130, 130, 128, 128, 128, 125, 125, 125, 125, 122, 122, 122, 122, 120, 120, 120, 120, 120, 117, 117, 117, 117, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115], dtype='uint8'),
                        np.array([255, 255, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 20, 23, 25, 33, 38, 40, 43, 48, 54, 59, 61, 64, 69, 77, 79, 82, 87, 92, 97, 99, 102, 107, 115, 120, 123, 125, 130, 138, 141, 143, 150, 156, 163, 165, 168, 173, 181, 186, 186, 187, 180, 176, 173, 169, 163, 157, 150, 146, 142, 136, 132, 126, 123, 119, 114, 108, 105, 101, 96, 93, 88, 84, 81, 77, 70, 68, 64, 60, 55, 49, 47, 45, 37, 33, 28, 24, 21, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype='uint8'))

        kwargs['output_info']['bandCount'] = 1            # output is a single band raster
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': maximumValue}, )  # we know something about the stats of the outgoing NBR raster.
        kwargs['output_info']['histogram'] = ()           # we know nothing about the histogram of the outgoing raster.
        kwargs['output_info']['pixelType'] = pixelType    # bit-depth of the outgoing NBR raster based on user-specified parameters
        kwargs['output_info']['colormap'] = colormap      # optional colormap if requesting for an color image
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r1_inBlock = pixelBlocks['r1_pixels']  # a two band raster extracted from raster input 1
        r2_inBlock = pixelBlocks['r2_pixels']  # a two band raster extracted from raster input 2

        r1_nir = np.array(r1_inBlock[0], dtype='f4')                  # extractbands ensures first band is Near Infrared.
        r1_swir = np.array(r1_inBlock[1], dtype='f4')                 # extractbands ensures second band is Shortwave Infrared
        r2_nir = np.array(r2_inBlock[0], dtype='f4')                  # extractbands ensures first band is Near Infrared of raster2.
        r2_swir = np.array(r2_inBlock[1], dtype='f4')                 # extractbands ensures second band is Shortwave Infrared of raster 2

        np.seterr(divide='ignore')
        r1_outBlock = (r1_nir - r1_swir) / (r1_swir + r1_nir)                      # compute NBR ((B4-B6)/(B4+B6)) for raster 1 - before fire NBR
        r2_outBlock = (r2_nir - r2_swir) / (r2_swir + r2_nir)                      # compute NBR ((B4-B6)/(B4+B6)) for raster 2 - after fire NBR
        outBlock = r1_outBlock - r2_outBlock                                       # compute delta NBR = before - after

        if self.applyScaling:
            outBlock = (outBlock * 100.0) + 100.0                  # apply a scale and offset to the the NBR, if needed.

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'               # outgoing raster is now 'Processed' 
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'NBR'
        return keyMetadata
