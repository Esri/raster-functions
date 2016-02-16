import numpy as np
import math


class FuzzyMembership():

    def __init__(self):
        self.name = "Fuzzy Membership Function"
        self.description = ("Reclassifies or transforms the input data to a 0 to 1 "
                            "scale based on the possibility of being a member of a "
                            "specified set")
        self.parA = {'minimum': 1., 'mid': None, 'meanMultipler': 1.}
        self.parB = {'maximum': 1., 'stdMultipler': 1., 'spreadA': 0.1, 'spreadB': 5.}

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ("Fuzzy Membership tool - 0 is assigned to those locations that "
                                "are definitely not a member of the specified set. "
                                "1 is assigned to those values that are definitely a member "
                                "of the specified set, and the entire range of possibilities "
                                "between 0 and 1 are assigned to some level of possible membership.")
            },
            {
                'name': 'mode',
                'dataType': 'string',
                'value': 'Linear',
                'required': True,
                'domain': ('Linear', 'Gaussian', 'Small', 'Large', 'Near', 'MSSmall', 'MSLarge'),
                'displayName': "Fuzzy Membership Type",
                'description': "Fuzzy Membership type."
            },
            {
                'name': 'par1',
                'dataType': 'numeric',
                'value': None,
                'required': False,
                'displayName': "Input Parameter A",
                'description': ("Linear : {minimum value}, Gaussian/Near/Small/Large : {mid point}, " 
                                "MSSmall/MSLarge : {mean multiplier}.")
            },
            {
                'name': 'par2',
                'dataType': 'numeric',
                'value': False,
                'required': True,
                'displayName': "Input Parameter B",
                'description': ("Linear : {maximum value}, Gaussian/Near/Small/Large : {spread}, "
                                "MSSmall/MSLarge : {std deviation multiplier}. ")
            },
            {
                'name': 'hedge',
                'dataType': 'string',
                'value': 'None',
                'required': False,
                'domain': ('None', 'Somewhat', 'Very'),
                'displayName': "Hedge",
                'description': ("A hedge increases or decreases the fuzzy membership values which modify the meaning of a fuzzy set. "
                                "None - No hedge applied. "
                                "Somewhat - The square root of the fuzzy membership function. Increases fuzzy membership functions. "
                                "Very- The square  of the fuzzy membership function. Decreases fuzzy membership functions.")
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,       # inherit everything but the pixel type (1)
          'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
          'inputMask': False                    # we don't need the input mask in .updatePixels()
        }

    def updateRasterInfo(self, **kwargs):
        # output raster information
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 1.0},)

        self.mode = kwargs['mode'].lower()  # input fuzzy membership mode
        self.hedge = kwargs['hedge']  # to modify fuzzy membership values

        # statistics of input raster
        stats = kwargs['raster_info']['statistics'][0]
        self.mean, self.std = stats['mean'], stats['standardDeviation']

        # assignment of fuzzy membership parameters
        if kwargs['par1'] != 0.0:
            self.parA = self.parA.fromkeys(self.parA, kwargs['par1'])
        else:
            self.parA['minimum'] = stats['minimum']
            self.parA['mid'] = (stats['minimum']+stats['maximum'])/2

        if kwargs['par2'] != 0.0:
            self.parB = self.parB.fromkeys(self.parB, kwargs['par2'])
        else:
            self.parB['maximum'] = stats['maximum']

        # check range of input range
        # linear fuzzy membership min - max
        if ((self.parA['minimum'] == self.parB['maximum']) and (self.mode == "linear")):
            raise Exception("Linear minimum and maximum must be different.")

        # spread values for fuzzy membership function
        if ((self.parB['spreadA'] < 0.01 or self.parB['spreadA'] > 1) and (self.mode == 'gauss' or self.mode == 'near')) or \
           ((self.parB['spreadB'] < 1 or self.parB['spreadB'] > 10) and (self.mode == 'large' or self.mode == 'small')):
            raise Exception("Spread value out of range.")

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input raster pixel block
        r = np.array(pixelBlocks['raster_pixels'], dtype='f8', copy=False)

        # fuzzy linear membership
        if self.mode == "linear":
            r = (r - self.parA['minimum']) / (self.parB['maximum'] - self.parA['minimum'])

        # fuzzy gaussian membership.
        elif self.mode == 'gaussian':
            r = (np.e)**((-self.parB['spreadA']) * ((r - self.parA['mid'])**2))

        # fuzzy large membership.
        elif self.mode == 'large':
            r = (1 / (1 + ((r / self.parA['mid'])**(-self.parB['spreadB']))))

        # fuzzy small membership.
        elif self.mode == 'small':
            r = (1 / (1 + ((r / self.parA['mid'])**(self.parB['spreadB']))))

        # fuzzy near membership.
        elif self.mode == 'near':
            r = (1 / (1 + (self.parB['spreadA'] * (r - self.parA['mid'])**2)))

        # fuzzy mssmall membership.
        elif self.mode == 'mssmall':
            rTemp = (self.parB['stdMultipler'] * self.std) / (r - (self.parA['meanMultipler'] * self.mean) + (self.parB['stdMultipler'] * self.std))
            np.putmask(r, r <= (self.mean * self.parA['meanMultipler']), 1.0)
            np.putmask(r, r > (self.mean * self.parA['meanMultipler']), rTemp)

        # fuzzy mslarge membership.
        else:
            rTemp = 1 - (self.parB['stdMultipler'] * self.std) / (r - (self.parA['meanMultipler'] * self.mean) + (self.parB['stdMultipler'] * self.std))
            np.putmask(r, r <= (self.mean * self.parA['meanMultipler']), 0.0)
            np.putmask(r, r > (self.mean * self.parA['meanMultipler']), rTemp)

        # clip output values between [0.0, 1.0]
        r = np.clip(r, 0.0, 1.0)

        # hedge calculations
        if (self.hedge == "SOMEWHAT"):  r = r ** 0.5
        elif (self.hedge == "VERY"):    r = r ** 2

        if len(r.shape) > 2:
            pixelBlocks['output_pixels'] = r[0].astype(props['pixelType'], copy=False)     # multi band raster
        else:
            pixelBlocks['output_pixels'] = r.astype(props['pixelType'], copy=False)        # single band raster

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'FuzzyMembership'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'FuzzyMembership'

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1]. Esri (2013): ArcGIS Resources. How Fuzzy Membership Works.
    http://resources.arcgis.com/en/help/main/10.1/index.html#//009z000000rz000000

    [2]. Esri (2013): ArcGIS Resources. An overview of fuzzy classes.
    http://resources.arcgis.com/en/help/main/10.1/index.html#/An_overview_of_fuzzy_classes/005m00000019000000/

"""
