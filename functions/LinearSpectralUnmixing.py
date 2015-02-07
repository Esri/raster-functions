import numpy as np

class LinearSpectralUnmixing():
    def __init__(self):
        self.name = 'Linear Spectral Unmixing'
        self.description = 'Performs linear spectral unmixing for a multiband raster.'
        self.inputSignatures = None # ultimately will be a dict
        self.coefficients = None    # ultimately will be a transposed np array


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
                'name': 'inputsignatures',
                'dataType': 'string',
                'value': '{\'Veg\': [16.91479, 19.83083, 14.53383,93.16165, 41.97619, 18.11779],'+
                    ' \'Shadow\': [17.78413, 11.62528, 5.50679, 8.22514, 0.72993, 0.14649],'+
                    ' \'NPV\': [17.45967, 17.11275, 16.30269, 26.19254, 40.90807, 45.67303],'+
                    ' \'Soil\': [50.17609, 60.45217, 67.33043,83.83261, 93.41739, 81.16739]}',
                'required': True,
                'displayName': 'Endmember Training Signature Means',
                'description': 'The training site means per each classification for each band'
            },
        ]


    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 1 | 2 | 4 | 8, # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,  # reset stats, histogram, key properties
            'inputMask': False
        }


    def updateRasterInfo(self, **kwargs):
        # get endmember input string value and convert to dict
        inputSignatures = kwargs['inputsignatures']
        self.inputSignatures = eval(inputSignatures)

        # convert input endmember signatures into arrays of each endmember across bands
        # [[vegB, vegG, vegR, ...], [shadowB, shadowG, shadowR, ...], [...]]
        signaturesArray = np.array(self.inputSignatures.values())

        # transpose signature axes to into arrays of each band's endmembers
        # [[vegB, shadowB, npvB, ...], [vegG, shadowG, npvG, ...], [...]]
        # assign to coefficients member var to use in np.linalg.lstsq()
        self.coefficients = signaturesArray.T

        # output bandCount is number of endmembers + 1 residuals raster
        bandCount = len(self.inputSignatures) + 1

        # rough estimation of output stats
        outStats = {'minimum': -10.0, 'maximum': 10.0, 'skipFactorX': 50, 'skipFactorY': 50}
        outStats = tuple(outStats for i in xrange(bandCount))

        kwargs['output_info']['bandCount'] = bandCount
        kwargs['output_info']['statistics'] = outStats
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['pixelType'] = 'f4'

        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input raster pixel block
        inBlock = pixelBlocks['raster_pixels']

        # transpose raster array axes into arrays of band values per pixel,
        # [B, G, R, NIR1, SWIR1, SWIR2] at each pixel
        inBlockT = inBlock.transpose([1, 2, 0])

        # reshape to slightly flatten to 2d array
        inBlockTFlat = inBlockT.reshape((-1, inBlockT.shape[-1]))

        # solve simultaneous equations with coefficients and each pixel stack
        # pixel stacks to solve must be transposed to (M,K) matrix of K columns
        results = np.linalg.lstsq(self.coefficients, inBlockTFlat.T)

        outBlockList = [arr.reshape(-1, inBlock.shape[-1]) for arr in results[0]]
        outBlockList.append(results[1].reshape(-1, inBlock.shape[-1]))

        pixelBlocks['output_pixels'] = np.array(outBlockList).astype(props['pixelType'])

        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            # dataset level
            keyMetadata['datatype'] = 'Processed'
        elif bandIndex == len(self.inputSignatures):
            # residuals raster
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Residuals'
        else:
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.inputSignatures.keys()[bandIndex]
        return keyMetadata
