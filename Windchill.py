import numpy as np


class Windchill():

    def __init__(self):
        self.name = "Windchill Function"
        self.description = "This function computes windchill on the Fahrenheit scale given wind-speed and temperature."


    def getParameterInfo(self):
        return [
            {
                'name': 'temperature',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Temperature Raster",
                'description': "A single-band raster where pixel values represent ambient air temperature in Fahrenheit."
            },
            {
                'name': 'ws',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Wind-speed Raster",
                'description': "A single-band raster where pixel values represent wind speed measured in miles per hour."
            },
        ]


    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,                       # inherit all but the pixel type from the input raster
          'invalidateProperties': 2 | 4 | 8,                    # invalidate statistics & histogram on the parent dataset because we modify pixel values. 
          'inputMask': False                                    # Don't need input raster mask in .updatePixels(). Simply use the inherited NoData. 
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1                  # output is a single band raster
        kwargs['output_info']['statistics'] = ()                # we know nothing about the stats of the outgoing raster. 
        kwargs['output_info']['histogram'] = ()                 # we know nothing about the histogram of the outgoing raster.
        kwargs['output_info']['pixelType'] = 'f4'
        return kwargs


    def updatePixels(self, tlc, size, props, **pixelBlocks):
        ws = np.array(pixelBlocks['ws_pixels'], dtype='f4')
        t = np.array(pixelBlocks['temperature_pixels'], dtype='f4')

        ws16 = np.power(ws, 0.16)
        outBlock = 35.74 + (0.6215 * t) - (35.75 * ws16) + (0.4275 * t * ws16)
        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['datatype'] = 'Windchill'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Winchill'
        return keyMetadata
