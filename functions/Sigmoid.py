from scipy.special import erf,erfc
import numpy as np


class Sigmoid():
    def __init__(self):
        self.name = "Error Function"
        self.description = "This function computes the Gauss Error function (erf) / Complementary Error Function (erfc) given a raster"
        self.op = None

    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "Input raster to compute Gauss Error Function (erf) / Complementary Error Function (erfc)."
            },
            {
                'name': 'op',
                'dataType': 'string',
                'value': 'Error Function',
                'required': False,
                'domain': ('Error Function', 'Complementary Error Function'),
                'displayName': "Function Choice",
                'description': "The method indicating choice of error function to be executed on the raster"
            },
        ]


    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 1| 2 | 4 | 8,           # inherit everything from the input raster
          'invalidateProperties': 2 | 4 ,              # invalidate histogram and statistics because we are modifying pixel values
        }

    def updateRasterInfo(self, **kwargs):
        m = kwargs.get('op', 'Error function').lower()  # user-specified input
        if m == 'error function':
            self.op = erf
        else:
            self.op = erfc

        kwargs['output_info']['pixelType'] = 'f4'      # output pixels are floating-point values
        kwargs['output_info']['statistics'] = ()       # clear stats.
        kwargs['output_info']['histogram'] = ()        # clear histogram.
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r1 = np.array(pixelBlocks['r1_pixels'], dtype='f4')       # get the input raster pixel block
        pixelBlocks['output_pixels'] = self.op(r1).astype(props['pixelType'])   # computation and assignment of output raster pixel block
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
