import numpy as np
import utils

class LinearSpectralUnmixing():

    def __init__(self):
        self.name = "Linear Spectral Unmixing"
        self.description = ("Computes the endmember abundance raster corresponding to a multiband "
                            "input raster by performing linear spectral unmixing.")
        self.signatures = None      # ultimately will be a dict
        self.coefficients = None    # ultimately will be a transposed np array
        self.applyScaling = False
        self.trace = utils.Trace()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster",
                'description': "The primary multi-band input raster to be classified."
            },
            {
                'name': 'signatures',
                'dataType': 'string',
                'value': ('{"Shadow": [70.05629, 27.24081, 25.31275, 24.17432, 31.77904, 17.82422], '
                          '"Veg": [65.46086, 30.09995, 26.27376, 117.45741, 76.96012, 26.25062], '
                          '"NPV": [74.74029, 32.06931, 35.57350, 32.66032, 73.63062, 60.51104], '
                          '"Soil": [143.65580, 79.30271, 102.82176, 93.60246, 176.57705, 117.49280]}'),
                'required': True,
                'displayName': "Endmember Training Signature Means",
                'description': ("The training site means for each endmember classification for each band. "
                                "Input value should adhere to Python dictionary or JSON formatting.")
            },
            {
                'name': 'method',
                'dataType': 'string',
                'value': 'Scaled',
                'required': True,
                'domain': ('Scaled', 'Raw'),
                'displayName': 'Output Image Type',
                'description': ('The type of output expected from this function. Specify "Scaled" for endmember '
                                'abundance values constrained between 0.0 - 1.0 along with a calculation of r-squared (R2). '
                                'Choose "Raw" for unaltered abundance values and residual sum of squares (RSS).')
            }
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
        s = kwargs['signatures']
        self.signatures = eval(s)

        # convert input endmember signatures into arrays of each endmember across bands
        # [[vegB, vegG, vegR, ...], [shadowB, shadowG, shadowR, ...], [...]]
        # ... and then transpose signature axes to into arrays of each band's endmembers
        # [[vegB, shadowB, npvB, ...], [vegG, shadowG, npvG, ...], [...]]
        # assign to coefficients member var to use in np.linalg.lstsq()
        self.coefficients = np.array(list(self.signatures.values())).T
        P = self.coefficients.shape
        outBandCount = 1 + P[1]             # endmembers + residuals
        self.trace.log(str(kwargs['raster_info']))
        inBandCount = kwargs['raster_info']['bandCount']
        if P[0] != inBandCount:
            raise Exception(("Incoming raster has {0} bands; endmember signatures "
                             "indicate {1} input bands.").format(inBandCount, P[0]))

        # determine output pixel value method
        self.applyScaling = kwargs['method'].lower() == 'scaled'
        outStats = {
            'minimum': 0. if self.applyScaling else -10.,
            'maximum': 1. if self.applyScaling else 10.,
            'skipFactorX': 10,
            'skipFactorY': 10
        }

        # repeat stats for all output raster bands
        kwargs['output_info']['statistics'] = tuple(outStats for i in range(outBandCount))
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['bandCount'] = outBandCount
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
            RSS = resid                                     # without modification, resid is in fact RSS
            TSS = np.sum((y - y.mean())**2, axis=0)         # total sum of squares
            R2 = 1 - RSS / TSS
            resid = R2.reshape(1, -1, inBlock.shape[-1])
        else:
            resid = resid.reshape(1, -1, inBlock.shape[-1]) # extra dimension to match shape of endmembers

        outBlocks = np.row_stack((endmembers, resid))       # resid can be either RSS or R2

        # output pixel arrays of abundances & residuals
        pixelBlocks['output_pixels'] = outBlocks.astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                                 # dataset level
            keyMetadata['datatype'] = 'Scientific'
        elif bandIndex == len(self.signatures):             # residuals band
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Residuals'
        else:                                               # endmember bands
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = list(self.signatures.keys())[bandIndex]
        return keyMetadata


## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:
    [1]. Adams, J.B., Sabol, D.E., Kapos, V., Filho, R.A., Roberts, D.A., Smith, M.O., 
         Gillespie, A.R., 1995. Classification of multispectral images based on fractions 
         of endmembers: application to land cover change in the Brazilian Amazon.
         Remote Sensing of Environment 52 (2), 137-154.
"""
