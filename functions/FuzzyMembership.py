import numpy as np
import math
import utils


class FuzzyMembership():

    def __init__(self):
        self.name = "Fuzzy Membership Function"
        self.description = "Reclassifies or transforms the input data to a 0 to 1 scale based on the possibility of being a member of a specified set"
        self.max, self.min = 1. , 1.                          # default values for fuzzy membership functions.
        self.spreadA, self.spreadB = 0.1 , 5.
        self.meanM, self.stdM = 1. , 1.
        self.trace = utils.Trace()

    def getParameterInfo(self):
        return [
             {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ("Fuzzy Membership tool - 0 is assigned to those locations that are definitely not a member of the specified set."
                                " 1 is assigned to those values that are definitely a member of the specified set,"
                                " and the entire range of possibilities between 0 and 1 are assigned to some level of possible membership")
            },
            {
                'name': 'op',
                'dataType': 'string',
                'value': 'Linear',
                'required': False,
                'domain': ('Linear','Gaussian','Small','Large','Near','MSSmall','MSLarge'),
                'displayName': "Fuzzy Membership Type",
                'description': "Select Fuzzy Membership type."
            },
            {
                'name': 'par1',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Parameter 1",
                'description': "Linear : {minimum value} , Gaussian/Near/Small/Large : {mid point} , MSSmall/MSLarge : {mean multiplier}. Enter 0 for default values."
            },
            {
                'name': 'par2',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Parameter 2",
                'description': "Linear : {maximum value} , Gaussian/Near/Small/Large : {spread} , MSSmall/MSLarge : {standard deviation multiplier}. Enter 0 for default values."
            },
            {
                'name': 'hedge',
                'dataType': 'string',
                'value': 'NONE',
                'required': False,
                'domain': ('NONE','SOMEWHAT','VERY'),
                'displayName': "Hedge",
                'description': ("A hedge increases or decreases the fuzzy membership values which modify the meaning of a fuzzy set."
                                " NONE - No hedge applied."
                                " SOMEWHAT - The square root of the fuzzy membership function. Increases fuzzy membership functions."
                                " VERY - The square  of the fuzzy membership function. Decreases fuzzy membership functions.")
            },

        ]


    def getConfiguration(self, **scalars):
        return {
          'extractBands': (0,),                 # we only need the first band.  Comma after zero ensures it's a tuple.
          'inheritProperties': 2 | 4 | 8,       # inherit everything but the pixel type (1)
          'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                         # no padding of the input pixel block
          'inputMask': False                    # we don't need the input mask in .updatePixels()
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 1.0},)
        kwargs['output_info']['histogram'] = ()

        self.op = kwargs.get('op', 'Linear').lower()
        self.hedge = kwargs.get('hedge','NONE')
        par1 = kwargs.get('par1', 0.0)
        par2 = kwargs.get('par2', 0.0)

        stats = kwargs['raster_info']['statistics'][0]
        self.mean, self.std = stats['mean'], stats['standardDeviation']

        ### Value assignment to parameters ###
        if(par1 == 0.0):
            self.mid, self.min, self.meanM = (stats['minimum']+stats['maximum'])/2 , stats['minimum'] , 1.0     # default values
        else:
            self.min = self.mid = self.meanM = par1

        if(par2 != 0.0):
            self.max = self.spreadA = self.spreadB = self.stdM = par2
        else:
            self.max, self.stdM, self.spreadA, self.spreadB = stats['maximum'], 1.0, 0.1, 5.0                  # default values

        ### Check range of parameters ###
        if ((self.spreadA < 0.01 or self.spreadA > 1) and (self.op == 'gauss' or self.op == 'near')) or \
           ((self.spreadB < 1 or self.spreadB > 10) and (self.op == 'large' or self.op == 'small'))  :
            raise Exception ("Spread value out of range.")
        if ((self.min == self.max) and (self.op == "linear")):
            raise Exception ("Linear minimum and maximum must be different.")

        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r = np.array(pixelBlocks['raster_pixels'], dtype='f8', copy=False)

        if self.op == 'linear':
            r = (r - self.min) / (self.max - self.min)             # fuzzy linear membership.

        elif self.op == 'gaussian':
            r = (np.e)**((-self.spreadA)*((r-self.mid)**2))        # fuzzy gaussian membership.

        elif self.op == 'large':
            r = (1/(1+((r/self.mid )**(-self.spreadB))))           # fuzzy large membership.
            self.trace.log("Trace|Mid: {0}|SpreadB: {1}".format(self.mid,self.spreadB))

        elif self.op == 'small':
            r = (1/(1+((r/self.mid)**(self.spreadB))))             # fuzzy small membership.

        elif self.op == 'near':
            r = (1/(1+(self.spreadA*(r-self.mid)**2)))             # fuzzy near membership.

        elif self.op == 'mssmall':                                 # fuzzy mssmall membership.
            self.trace.log("Trace|StdM: {0}|MeanM: {1}|Std: {2}|Mean: {3}".format(self.stdM,self.meanM,self.std,self.mean))

            rtemp = (self.stdM * self.std) / (r - (self.meanM * self.mean) + (self.stdM * self.std))
            np.putmask(r, r <=(self.mean*self.meanM), 1.0)
            np.putmask(r, r >(self.mean*self.meanM),rtemp)

        else:                                                      # fuzzy mslarge membership.
            rtemp = 1- (self.stdM * self.std) / (r - (self.meanM * self.mean) + (self.stdM * self.std))
            np.putmask(r, r <=(self.mean*self.meanM), 0.0)
            np.putmask(r, r >(self.mean*self.meanM),rtemp)

        np.putmask(r, r < 0.0, 0.0)
        np.putmask(r, r > 1.0, 1.0)

        if (self.hedge == "SOMEWHAT"):      # hedge calculations
            r = r ** 0.5
        elif (self.hedge == "VERY"):
            r = r ** 2

        pixelBlocks['output_pixels'] = r.astype(props['pixelType'], copy=False)        # single band output raster

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
       if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'FuzzyMembership'
       elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'FuzzyMembership'

"""
References:
    [1]. Esri (2013): ArcGIS Resources. How Fuzzy Membership Works.
    http://resources.arcgis.com/en/help/main/10.1/index.html#//009z000000rz000000
    [2]. Esri (2013): ArcGIS Resources. An overview of fuzzy classes.
    http://resources.arcgis.com/en/help/main/10.1/index.html#/An_overview_of_fuzzy_classes/005m00000019000000/
"""
