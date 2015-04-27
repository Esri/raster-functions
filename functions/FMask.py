import numpy as np
import math
from scipy import ndimage as ndi

class FMask():

    def __init__(self):
        self.name = "FMask Function"
        self.description = " FMask (Function of Mask) - Used for cloud & cloud shadow detection in Landsat imagery"

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Landsat Composite Bands",
                'description': ("Landsat Imagery. Nth Band - Thermal Band")
            },
            {
                'name': 'type',
                'dataType': 'string',
                'value': 'Landsat 8',
                'required': True,
                'domain': ('Landsat 5', 'Landsat 7', 'Landsat 8'),
                'displayName': "Landsat Scene",
                'description': "Landsat Scene Input for F-Mask Function"
            },
            {
                'name': 'mode',
                'dataType': 'string',
                'value': 'Cloud',
                'required': True,
                'domain': ('Cloud', 'Cloud Shadow', 'Snow'),
                'displayName': "Masking Feature",
                'description': "Mask feature from Landsat Scene"
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,            # inherit everything but the pixel type (1) and no Data (2)
          'invalidateProperties': 2 | 4 | 8,     # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                          # no padding on each of the input pixel block
          'inputMask': False                     # we don't need the input mask in .updatePixels()
        }

    def updateRasterInfo(self, **kwargs):
        ## Input Parameters ##
        self.prepare(scene=kwargs.get("type","Landsat 8"),
                     mode=kwargs.get("mode", "Cloud"),)

        if self.scene == "Landsat 8":
            kwargs['output_info']['bandCount'] =  9
        else:
            kwargs['output_info']['bandCount'] =  7

        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['statistics'] = ({'minimum': 1, 'maximum':1})
        kwargs['output_info']['noData'] = np.array([255])

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        landsat     = np.array(pixelBlocks['raster_pixels'], dtype ='f4', copy=False)
        fmask       = np.zeros(landsat.shape)

        ## calculate dependent variables ##
        landsat      = self.convertScene(landsat)
        self.NDSI    = self.calculateNDSI(landsat)
        self.NDVI    = self.calculateNDVI(landsat)

        ## perform masking operation ##
        if self.mode == "Cloud":
            self.PCP     = self.potentialCloudPixels(landsat)
            output       = self.potentialCloudLayer(landsat)
            output       = self.neighborhoodTest(output)

        elif self.mode == "Snow":
            output      = self.potentialSnowLayer(landsat)
            output      = self.neighborhoodTest(output)

        else:
            output     = self.potentialCloudShadowLayer(landsat)

        for band in xrange(landsat.shape[0]):
            fmask[band]     = np.where(output  , 255 , landsat[band])

        pixelBlocks['output_pixels'] = fmask.astype('f4', copy=False)

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'FMask'
        return keyMetadata

 # ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
    # public methods...

    def prepare(self, scene = "Landsat 8", mode = "Cloud"):
        # K1 , K2 Thermal Conversion Constant
        self.scene = scene
        self.mode = mode
        if scene == "Landsat 8":
            self.k1 , self.k2  = 774.89 , 1321.08
           # self.k1 , self.k2  = 480.89 , 1201.14   Band 11 Thermal Constants
            self.lmax , self.lmin = 22.00180 ,  0.10033
            self.dn = 65534
            self.BI = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        elif scene == "Landsat 7":
            self.k1, self.k2 = 666.09 , 1282.71
            self.lmax , self.lmin = 17.04 , 0.0
            self.dn = 244
            self.BI = [0, 1, 2, 3, 4, 5, 6]

        else:
            self.k1, self.k2 = 607.76 , 1260.56
            self.lmax , self.lmin = 15.303 , 1.238
            self.dn = 244
            self.BI = [0, 1, 2, 3, 4, 5, 6]


    # Calculate Brightness Temperature from Thermal Bands
    def convertScene(self, landsat):
        if landsat.shape[0] == 7:
            start = 0
            finish = 6

        else:
            start = 1
            finish = 7

        landsat[-1] = ((self.lmax - self.lmin) / self.dn) * landsat[-1] + self.lmin
        landsat[-1] = ((self.k2/np.log((self.k1/landsat[-1])+1)) )

        for band in xrange(start, finish):
            landsat[band] *= (10**4)

        return landsat

    # 1. Calculate NDVI
    def calculateNDVI(self, landsat):
        NDVI     = (landsat[self.BI[3]] - landsat[self.BI[2]])/(landsat[self.BI[3]] + landsat[self.BI[2]])
        NDVI[(landsat[self.BI[3]]+landsat[self.BI[2]]) == 0] = 0.01

        return NDVI

    # 2. Calculate NDSI
    def calculateNDSI(self, landsat):
        NDSI     = (landsat[self.BI[1]] - landsat[self.BI[4]])/(landsat[self.BI[1]] + landsat[self.BI[4]])
        NDSI[(landsat[self.BI[1]]+landsat[self.BI[4]]) == 0] = 0.01

        return NDSI

    # 3. Saturation Test in Visible Bands
    def saturationTest(self, landsat):
        return np.greater((landsat[self.BI[0]]+landsat[self.BI[1]]+landsat[self.BI[2]]), 0)


    ## PASS 1. POTENTIAL CLOUD PIXELS ##
    # 4. Potential Cloud Pixels
    def potentialCloudPixels(self, landsat):
        PCP     = np.logical_and(np.logical_and(self.basicTest(landsat),self.whitenessTest(landsat)),\
                  np.logical_or(np.logical_and(self.hotTest(landsat),self.swirnirTest(landsat)),self.cirrusTest(landsat)))

        return PCP

    ## PASS 2. POTENTIAL SNOW LAYER ##
    # 5. Potential Snow Layer
    def potentialSnowLayer(self, landsat):
        PSL         = np.logical_or(np.logical_and(np.greater(self.NDSI, 0.15),np.logical_and(np.greater(landsat[self.BI[3]], 1100),\
                          np.greater(landsat[self.BI[1]], 1000))),np.less(100 * (landsat[-1]-273.15), 400))

        return PSL


    ## PASS 3. POTENTIAL CLOUD LAYER ##
    # 6. Potential Cloud Layer
    def potentialCloudLayer(self, landsat):
        waterTestValue = self.waterTest(landsat)

        condition1 = np.logical_and(np.logical_and(self.PCP,np.logical_not(waterTestValue)),np.greater(self.finalProbLand(landsat),self.clr_max))

        condition2 = np.logical_and(np.logical_and(self.PCP,waterTestValue),np.greater(self.finalProbWater(landsat),self.wclr_max))

        condition3 = np.less(100 * (landsat[-1] - 273.15), 1000)

        PCL         = np.logical_or(np.logical_or(condition1, condition2), condition3)

        return PCL

    # 6. Neighborhood Test
    def neighborhoodTest(self, pixels):
        pixels       = np.where(pixels, 1 , 0)
        pixelCount   = ndi.generic_filter(pixels, np.count_nonzero, size = 3)
        pixels       = np.where(np.logical_or(np.greater_equal(pixelCount, 4), np.equal(pixels, 1)), True, False)

        return pixels

    ## SPECTRAL TESTS ##
    # 7. Basic Test
    def basicTest(self, landsat):
        tempTest  ,band7Test = np.less(landsat[-1], 300) , np.greater(landsat[self.BI[5]],300)
        ndsiTest  , ndviTest = np.less(self.NDSI, 0.8) , np.less(self.NDVI,0.8)
        basicTest  = np.logical_and(band7Test, np.logical_and(ndsiTest, ndviTest))

        return basicTest

    # 8. Whiteness Test
    def whitenessTest(self, landsat):
        meanVis         = (landsat[self.BI[0]] + landsat[self.BI[1]] + landsat[self.BI[2]]) / 3
        whiteness       = (np.abs(landsat[self.BI[0]] - meanVis) + np.abs(landsat[self.BI[1]] - meanVis) + np.abs(landsat[self.BI[2]] - meanVis)) / meanVis
        whiteness       = np.where(self.saturationTest(landsat), 0, whiteness)
        whitenessTest   = np.less(whiteness , 0.7)

        return whitenessTest

    # 9. Haze Optimized Transformation - HOT Test
    def hotTest(self, landsat):
        return (np.logical_or(np.greater((landsat[self.BI[0]] - 0.5 * landsat[self.BI[2]] - 800) , 0), self.saturationTest(landsat)))

     # 10. SWIR-NIR Test
    def swirnirTest(self, landsat):
        return np.greater((landsat[self.BI[3]] / landsat[self.BI[4]]) , 0.75)

    # 11. Cirrus Test
    def cirrusTest(self, landsat):
        return np.greater(self.cirrusProbability(landsat),0.25)

     # 12. Water Test
    def waterTest(self, landsat):
        ndviTest_1  , ndviTest_2   = np.less(self.NDVI, 0.01) , np.less(self.NDVI, 0.1)
        band4Test_1 , band4Test_2  = np.less(landsat[self.BI[3]], 1100) , np.less(landsat[self.BI[3]], 500)

        waterTest                  = np.logical_or(np.logical_and(ndviTest_1 , band4Test_1), \
                                     np.logical_and(ndviTest_2  , band4Test_2))

        return waterTest

    ## END OF SPECTRAL TESTS ##


    ### WATER PIXEL TESTS ###
    # 13. Cirrus Probability
    def cirrusProbability(self, landsat):
        if self.scene == "Landsat 8":
            return np.divide(landsat[-2], 400)

        else:
            return np.zeros(landsat[0].shape)

    # 14. Brightness Probability
    def brightnessProbTest(self, landsat):
        brightnessTest = landsat[self.BI[4]] / 1100

        return np.clip(brightnessTest, 0, 1)

    # 15. Water Probability
    def finalProbWater(self,landsat):
        waterTest    = self.waterTest(landsat)
        idwt         = np.logical_and(np.logical_and(np.equal(self.PCP,False), waterTest),\
                       np.less_equal(landsat[self.BI[5]],300))

        tWater      = landsat[-1][idwt]

        if len(tWater) == 0:
            self.wclr_max = 27.5
        else:
            self.wclr_max     = np.percentile(tWater, 82.5)

        wtemp_Prob = (self.wclr_max - landsat[-1])/ 400.0
        wfinal_Prob  = 100 * wtemp_Prob * self.brightnessProbTest(landsat)

        return wfinal_Prob



    ### END OF WATER PIXEL TESTS ###

    ### LAND SPECTRAL TESTS ###
    # 16. Variability Probability
    def varProbability(self, landsat):
        sat_B2          = np.greater(landsat[self.BI[1]],0)
        sat_B3          = np.greater(landsat[self.BI[2]],0)

        modNDVI         = np.where(np.logical_and(sat_B3,np.greater(self.NDVI, 0)), 0, self.NDVI)
        modNDSI         = np.where(np.logical_and(sat_B2,np.less(self.NDSI, 0)), 0, self.NDSI)

        variabilityProb = 1 - np.maximum(np.maximum(np.abs(modNDVI), np.abs(modNDSI)), self.whitenessTest(landsat))

        return variabilityProb

    # 17. Land Probability
    def finalProbLand(self, landsat):

        waterTest    = self.waterTest(landsat)
        idlnd        = np.logical_and(np.equal(self.PCP,False),np.equal(waterTest,False))
        final_prob   = 100 * self.varProbability(landsat) + 100 * self.cirrusProbability(landsat)

        if len(final_prob[idlnd]) == 0:
            self.clr_max    = 27.5
        else:
            self.clr_max    = np.percentile(final_prob[idlnd], 82.5) + 0.225


        return final_prob

