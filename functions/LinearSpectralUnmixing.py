import numpy as np

class LinearSpectralUnmixing():
    def __init__(self):
        self.name = 'Linear Spectral Unmixing'
        self.description = 'Performs linear spectral unmixing for a multiband raster.'
        self.signatures = '{}'


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Raster',
                'description': 'The primary multi-band input raster to be classified'
            },
            {
                'name': 'signatures',
                'dataType': 'string',
                'value': '{\'veg\': [16.91479, 19.83083, 14.53383,93.16165, 41.97619, 18.11779],'+
                    ' \'shadow\': [17.78413, 11.62528, 5.50679, 8.22514, 0.72993, 0.14649],'+
                    ' \'npv\': [17.45967, 17.11275, 16.30269, 26.19254, 40.90807, 45.67303],'+
                    ' \'soil\': [50.17609, 60.45217, 67.33043,83.83261, 93.41739, 81.16739]}',
                'required': True,
                'displayName': 'Endmember Training Signature Means',
                'description': 'The training site means per each classification for each band'
            },
        ]


    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 1 | 2| 4 | 8,    # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,    # reset stats, histogram, key properties
            'inputMask': False                    # no input raster mask
        }


    def updateRasterInfo(self, **kwargs):
        signatures = kwargs['signatures'] # get endmember input string value
        self.signatures = eval(signatures) # convert to python dict

        # output bandCount is number of endmembers + 1 residuals raster
        bandCount = len(self.signatures) + 1
        print bandCount

        kwargs['output_info']['bandCount'] = bandCount
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()

        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # convert endmember signature means into numpy ndarray
        # must also transpose signatures so that you have an array of endmember mean values for B, G, R, etc.
        signatures = np.array([i for i in self.signatures.values()])
        signaturesT = signatures.T

        # get the input raster pixel block
        inBlock = pixelBlocks['raster_pixels']

        # transpose image ndarray axes so that you have an array of band values per pixel,
        # e.g.: [B, G, R, NIR1, NIR2, MIR] for each pixel
        inBlockT = inBlock.transpose([1, 2, 0])

        ## TO DO: this only works for 1 pixel at a time, specified by [row][col]
        ## assuming that inBlockT has correctly accessed a numpy ndarray
        pixel = inBlockT[0][0]
        # solve simultaneous equations with numpy linear algebra least squares
        results = np.linalg.lstsq(signaturesT, pixel)

        ## TO DO:
        ## results[0] is a list of the endmembers solutions at a given pixel
        ## self.signatures.keys() should be the corresponding order of endmembers for reference
        ## results[1] is the sum of residuals
        ## must rebuild outBlock into nEndmember "bands" + residual "band"

        outBlock = inBlock # a placeholder for now

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'])
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            # dataset level
            keyMetadata['datatype'] = 'Processed'
        elif bandIndex == len(self.signatures):
            # residuals raster
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Residuals'
        else:
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.signatures.keys()[bandIndex]
        return keyMetadata
