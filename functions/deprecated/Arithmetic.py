import numpy as np


class Arithmetic():
    def __init__(self):
        self.name = "Arithmetic Function"
        self.description = "Performs simple arithmetic operations on two rasters."
        self.op = None

    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster A",
                'description': ""
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster B",
                'description': ""
            },
            {
                'name': 'op',
                'dataType': 'string',
                'value': 'Add',
                'required': False,
                'domain': ('Add', 'Subtract', 'Multiply', 'Divide'),
                'displayName': "Operation",
                'description': ""
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 2 | 4 | 8,
            'invalidateProperties': 2 | 4 | 8,
            'resampling': True                                  # process at request resolution
        }

    def updateRasterInfo(self, **kwargs):
        m = kwargs.get('op', 'Add').lower()

        if m == 'add':          self.op = np.add
        elif m == 'subtract':   self.op = np.subtract
        elif m == 'multiply':   self.op = np.multiply
        elif m == 'divide':     self.op = np.divide

        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r1 = np.array(pixelBlocks['r1_pixels'], dtype='f4', copy=False)
        r2 = np.array(pixelBlocks['r2_pixels'], dtype='f4', copy=False)

        np.seterr(divide='ignore')
        pixelBlocks['output_pixels'] = self.op(r1, r2).astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'               # outgoing raster is now 'Processed'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
        return keyMetadata
