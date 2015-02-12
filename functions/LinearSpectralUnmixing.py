import numpy as np

class LinearSpectralUnmixing():
    def __init__(self):
        self.name = 'Linear Spectral Unmixing'
        self.description = 'Performs linear spectral unmixing for a multiband raster.'
        self.inputSignatures = None     # ultimately will be a dict
        self.coefficients = None        # ultimately will be a transposed np array
        self.applyScaling = False


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
                'value': ('{"Shadow": [70.05629, 27.24081, 25.31275, 24.17432, 31.77904, 17.82422], '
                          '"Veg": [65.46086, 30.09995, 26.27376, 117.45741, 76.96012, 26.25062], '
                          '"NPV": [74.74029, 32.06931, 35.57350, 32.66032, 73.63062, 60.51104], '
                          '"Soil": [143.65580, 79.30271, 102.82176, 93.60246, 176.57705, 117.49280]}'),
                'required': True,
                'displayName': 'Endmember Training Signature Means',
                'description': ('The training site means for each endmember classification for each band. '
                                'Input value should adhere to Python dictionary or JSON formatting.')
            },
            {
                'name': 'method',
                'dataType': 'string',
                'value': 'Scaled',
                'required': True,
                'domain': ('Scaled', 'Raw'),
                'displayName': 'Output Image Type',
                'description': ('The type of output expected from this function. Specify "Scaled" for endmember '
                                'solution values constrained between 0.0 - 1.0 along with a calculation of r-squared (R2). '
                                'Choose "Raw" for unaltered endmember solution values and residual sum of squares (RSS).')
            },
        ]


    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,      # reset stats, histogram, key properties
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

        # determine output pixel value method
        method = kwargs['method'].lower()
        if method == 'scaled':
            # constrained output pixels
            self.applyScaling = True
            outStats = {'minimum': 0, 'maximum': 1.0, 'skipFactorX': 10, 'skipFactorY': 10}
        else:
            self.applyScaling = False
            # rough estimation of output stats
            outStats = {'minimum': -10.0, 'maximum': 10.0, 'skipFactorX': 10, 'skipFactorY': 10}
        # repeat stats for all output raster bands
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

        # reshape to slightly flatten to 2d array,
        # and pixel stacks to solve must be transposed to (M,K) matrix of K columns
        y = inBlockT.reshape(-1, inBlockT.shape[-1]).T

        # solve simultaneous equations with coefficients and each pixel stack
        # store the model solution and residual sum of squares (RSS)
        model, resid = np.linalg.lstsq(self.coefficients, y)[:2]

        endmembers = np.array([endmember.reshape(-1, inBlock.shape[-1]) for endmember in model])
        if self.applyScaling:
            # clip negative values and scale from 0.0 to 1.0
            endmembers.clip(min=0, out=endmembers)
            endmembers *= (1.0 / endmembers.max())

            # calculate R2
            RSS = resid                                 # without modification, resid is in fact RSS
            TSS = np.sum((y - y.mean())**2, axis=0)     # total sum of squares
            R2 = 1 - RSS / TSS
            resid = R2.reshape(1, -1, inBlock.shape[-1])
        else:
            resid = resid.reshape(1, -1, inBlock.shape[-1])  # extra dimension to match shape of endmembers

        outBlocks = np.row_stack((endmembers, resid))   # resid can be either RSS or R2

        # output pixel arrays of endmembers & residuals
        pixelBlocks['output_pixels'] = outBlocks.astype(props['pixelType'])

        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            # dataset level
            keyMetadata['datatype'] = 'Processed'
        elif bandIndex == len(self.inputSignatures):
            # residuals band
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Residuals'
        else:
            # endmember bands
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.inputSignatures.keys()[bandIndex]
        return keyMetadata
