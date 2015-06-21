import math
import numpy as np
from scipy import ndimage as ndi


class Contour():

    def __init__(self):
        self.name = "Contour Function"
        self.description = ("Contour Raster Function generates contour lines "
                            "i.e. line joining the points with the same elevation"
                            "from the given DEM raster.")
        self.par = {}  # a dict for input parameters.
        self.noData = None  # store the noData of the input raster.
        self.minValue = None  # minimum of the input raster.

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "DEM",
                'description': "A DEM Raster where each pixel stores the elevation of a particular point."
            },
            {
                'name': 'mode',
                'dataType': 'string',
                'value': 'Contour',
                'required': True,
                'domain': ('Contour', 'Smooth Contour', 'Fill', 'Smooth Fill', 'Smoothing Only'),
                'displayName': "Mode",
                'description': "Select Mode for Contour Function."
            },
            {
                'name': 'values',
                'dataType': 'string',
                'value': 'No. of Contours',
                'required': True,
                'domain': ('No. of Contours', 'Contour Interval'),
                'displayName': "Draw",
                'description': "No. of Contour: Signifies the average number of contour lines the user wants to see."
                               "Contour Interval: To specify the difference in elevation between two consecutive."
            },
            {
                'name': 'interval',
                'dataType': 'numeric',
                'value': 10.0,
                'required': True,
                'displayName': "Draw Value",
                'description': "Input Draw Mode Value."
            },
            {
                'name': 'base',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Contour Base",
                'description': "The starting value from which contour lines are calculated. Contours below the base elevation value are not drawn."
            },
            {
                'name': 'indexcontour',
                'dataType': 'boolean',
                'value': True,
                'displayName': "Index Contour",
                'description': "If enabled, every 5th contour line is thicker than the rest."
            },
            {
                'name': 'sfactor',
                'dataType': 'numeric',
                'value': 0.6,
                'required': True,
                'displayName': "Smoothing Factor",
                'description': "Defines how much smoothing to apply. Higher the value, more the smoothing."
            },
            {
                'name': 'zfactor',
                'dataType': 'numeric',
                'value': 1.0,
                'required': True,
                'displayName': "Z-Factor",
                'description': "Z-Factor for Advanced Smoothing."
            },
            {
                'name': 'sloperad',
                'dataType': 'numeric',
                'value': 3.0,
                'required': True,
                'displayName': "Smooth Slope Radius",
                'description': "Filter used to ensure that the tops of mountains do not get flattened."
            },
            {
                'name': 'avgrad',
                'dataType': 'numeric',
                'value': 6.0,
                'required': True,
                'displayName': "Average Radius",
                'description': "Radius used to smooth possible kinks at the edges between flat and hilly terrain."
            },
            {
                'name': 'radinc',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Radius Increase",
                'description': "Increases the smoothing, specifically for steeper areas."
            },
            {
                'name': 'maxrad',
                'dataType': 'numeric',
                'value': 6.0,
                'required': True,
                'displayName': "Maximum Radius",
                'description': "Limits the amount of smoothing."
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,             # inherit everything except pixelType (1) and noData value (2)
            'invalidateProperties': 2 | 4 | 8,      # invalidate these aspects because we are modifying pixel values and updating key properties.
            'padding': 0,                           # no padding on each of the input pixel block
            'inputMask': False                      # we don't need the input mask in .updatePixels()
        }

    def updateRasterInfo(self, **kwargs):
        r = kwargs['raster_info']

        if r['bandCount'] > 1:
            raise Exception("Input raster has more than one band. Only single-band raster datasets are supported")

        # output raster information
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['resampling'] = True
        kwargs['output_info']['noData'] = self.assignNoData(r['pixelType']) if not(r['noData']) else r['noData']
        kwargs['output_info']['pixelType'] = r['pixelType']

        try:     minValue = r['statistics'][0]['minimum']
        except:  minValue = None

        # prepare input parameters
        self.prepare(mode=kwargs['mode'], contourChoice=kwargs['values'], interval=kwargs['interval'], indexContour=kwargs['indexcontour'],
                     base=kwargs['base'], smootheningFactor=kwargs['sfactor'], zFactor=kwargs['zfactor'], slopeRadius=kwargs['sloperad'],
                     averageRadius=kwargs['avgrad'], radiusIncrease=kwargs['radinc'], maxRadius=math.ceil(kwargs['maxrad']), minValue=minValue)

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        dem = np.array(pixelBlocks['raster_pixels'], dtype='f8', copy=False)  # get the input raster pixel block

        # set raster properties to variables
        self.noData = self.assignNoData(props['pixelType']) if not(props['noData']) else props['noData']

        # enable dynamic contouring
        if self.par["contourChoice"] == "No. of Contours":
            self.dynamicContouring(dem)

        # apply function mode
        if self.par["mode"] == "Contour":  dem = self.generateContour(dem)  # Contour Mode
        elif self.par["mode"] == "Fill":   dem = self.fillMode(dem)  # Fill Mode
        else:                              dem = self.smoothRaster(dem)  # Smoothening Mode

        pixelBlocks['output_pixels'] = dem.astype(props['pixelType'], copy=False)  # output pixel array

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.par['mode']
        return keyMetadata

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
# other public methods...

    def prepare(self, mode="Contour", contourChoice="No.of Contours", interval=10.0, base=0.0,
                indexContour=True, smootheningFactor=0.6, zFactor=1.0, slopeRadius=3.0,
                averageRadius=6.0, radiusIncrease=0.0, maxRadius=6.0, minValue=None):
        # assign input parameters
        self.par = {'mode': mode, 'contourChoice': contourChoice, 'interval': interval, 'orgInterval': interval, 'base': base,
                    'indexContour': indexContour, 'smootheningFactor': smootheningFactor, 'zFactor': zFactor, 'slopeRadius': slopeRadius,
                    'averageRadius': averageRadius, 'radiusIncrease': radiusIncrease, 'maxRadius': maxRadius}
        self.minValue = minValue

        # darken every 5th contour line
        self.par['indexContourFactor'] = 5 if indexContour else 1
        self.par["maximumRadius"] = int(math.ceil(max(max(averageRadius, maxRadius), slopeRadius)))

        # check range of parameters
        if smootheningFactor < 0.1 or smootheningFactor > 10 and (mode != "Contour" and mode != "Fill"):
            raise Exception("Smoothing Factor Out of Range.")

        if mode != "Contour" and mode != "Fill":
            if ((slopeRadius < 0.1 or slopeRadius > 5) or (averageRadius < 1 or averageRadius > 10) or
               (radiusIncrease < 0 or radiusIncrease > 10) or (maxRadius < 5 or maxRadius > 20)):
                raise Exception("Check Input Parameters - Out of Range Exception.")

    # assign noData value to output raster
    def assignNoData(self, pixelType):
        # assign noData depending on input pixelType
        if pixelType == 'f4':    return np.array([-3.4028235e+038, ])  # float 32 bit
        elif pixelType == 'i4':  return np.array([65535, ])  # signed integer 32 bit
        elif pixelType == 'i2':  return np.array([32767, ])  # signed integer 16 bit
        elif pixelType == 'i1':  return np.array([255, ])  # signed integer 8 bit
        elif pixelType == 'u4':  return np.array([-65536, ])  # unsigned integer 32 bit
        elif pixelType == 'u2':  return np.array([-32768, ])  # unsigned integer 16 bit
        elif pixelType == 'u1':  return np.array([-256, ])  # unsigned integer 8 bit

    # get minimum of input pixel block
    def calcRasterMin(self, dem):
        dem = np.ma.array(np.ma.masked_invalid(dem), mask=np.ma.masked_invalid(dem) == self.noData)  # mask noData values in raster
        return np.ma.min(np.ma.masked_invalid(dem))

    # dynamic contouring - interval calculation
    def dynamicContouring(self, dem):
        # mask noData values in raster
        dem = np.ma.array(np.ma.masked_invalid(dem), mask=np.ma.masked_invalid(dem) == self.noData)

        stdPixels = np.ma.std(np.ma.masked_invalid(dem))  # standard deviation of masked input
        maxPixels = np.ma.max(np.ma.masked_invalid(dem))  # maximum value of masked input
        minPixels = np.ma.min(np.ma.masked_invalid(dem))  # minimum value of masked input

        self.minScale = minPixels
        self.maxScale = maxPixels

        range1 = maxPixels - minPixels
        range2 = 5 * stdPixels
        range3 = max(range1, range2)

        cf = mod = m = 0
        try:        cf = math.floor((math.log10(range3 / self.par["orgInterval"]) * 3) + 0.5)
        except:     cf = 0
        mod = long(cf % 3)

        if mod == 0:    m = 1
        elif mod == 1:  m = 2
        elif mod == 2:  m = 5

        # new dynamic contour interval
        self.par["interval"] = max(1, m * (10**(math.floor(cf/3))))

    # intermediate contour value
    def calculateContourIntermediate(self, temp):
        return np.where(np.equal(temp, self.noData), self.noData, np.floor((temp - self.par["base"])/self.par["interval"]))

    # final contour value
    def finalContourValue(self, temp):
        return np.where(np.equal(temp, self.noData), self.noData, (temp * self.par["interval"]) + self.par["base"])

    # fill mode
    def fillMode(self, temp):
        # calculate intermediate contour values
        intermediateContourValue = self.calculateContourIntermediate(temp)

        # calculate final fill values
        finalFillValue = self.finalContourValue(intermediateContourValue)

        # substitute fill values
        dem = np.where((finalFillValue - self.par["base"]) <= 0, self.noData, finalFillValue)

        return dem

    # smooth raster
    def smoothRaster(self, temp):
        # steps for smooth raster
        # 1. initialize radius grid
        # 2. apply smooth radius grid
        # 3. apply average radius grid
        # 4. smoothen DEM

        # get minimum value of raster
        # required for smoothening
        self.minValue = self.calcRasterMin(temp) if not(self.minValue) else self.minValue

        # S1. initialize radius grid
        radiusGrid = self.initializeGrid(temp)

        # S2. apply smooth radius grid
        kernelSlope = self.radiusGridKernel(self.par["slopeRadius"])
        if self.par["slopeRadius"] > 1:
            radiusGrid = ndi.minimum_filter(radiusGrid, footprint=kernelSlope)

        # S3. apply average radius grid
        kernelAvg = self.radiusGridKernel(self.par["averageRadius"])
        noOfPixels = len(kernelAvg[kernelAvg == 1])
        if self.par["averageRadius"] > 1:
            radiusGrid = ndi.convolve(radiusGrid, kernelAvg) / noOfPixels

        # S4. smoothen DEM
        dem = self.smoothenDEM(temp, radiusGrid)

        # apply selected mode for smoothening
        if self.par["mode"] == "Smooth Contour":   dem = self.generateContour(dem)
        elif self.par["mode"] == "Smooth Fill":    dem = self.fillMode(dem)
        else:                                      dem = dem

        return dem

    # radius grid kernel
    def radiusGridKernel(self, radius):
        mRadius = int(math.ceil(radius))
        kernel = np.zeros((2 * mRadius + 1, 2 * mRadius + 1))
        y, x = np.ogrid[-mRadius:mRadius + 1, -mRadius:mRadius + 1]
        mask = x**2 + y**2 <= mRadius**2
        kernel[mask] = 1

        return kernel

    # initialize grid for smoothening
    def initializeGrid(self, temp):
        # applying z-factor before any smoothing
        temp = np.where(np.not_equal(temp, self.noData), temp * self.par["zFactor"], temp)

        # obtaining the slope of each pixel within the block
        xKernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        yKernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

        deltaX = ndi.convolve(temp, xKernel)
        deltaY = ndi.convolve(temp, yKernel)

        slopeTangent = np.sqrt(deltaX * deltaX + deltaY * deltaY) / 8

        # final assignment value
        mTemp = self.par["interval"] * self.par["smootheningFactor"] / slopeTangent + self.par["radiusIncrease"]

        # assigning the radius grid to each pixel
        temp = np.where(np.equal(temp, self.noData), self.par["maxRadius"], temp)

        cond = np.logical_and(np.not_equal(temp, self.noData), np.equal(slopeTangent, 0))
        radiusGrid = np.where(cond, self.par["maxRadius"], mTemp)

        # limiting the radius grid between 0 - maximumRadius
        radiusGrid = np.clip(radiusGrid, 0, self.par["maxRadius"])

        return radiusGrid

    # smoothen dem
    def smoothenDEM(self, temp, radiusGrid):
        maximumRadius = self.par["maximumRadius"] + 1
        radiusGrid = np.floor(radiusGrid).astype(int)
        avgGrid = np.empty((maximumRadius, temp.shape[0], temp.shape[1]))
        avgTemp = np.copy(temp)

        # average neighboring pixels for radius from 0 - maximumRadius
        for grid in xrange(int(maximumRadius)):
            kernel = self.radiusGridKernel(grid)
            noOfPixels = len(kernel[kernel == 1])
            avgGrid[grid] = ndi.convolve(temp, kernel) / noOfPixels

        for radius in xrange(int(maximumRadius)):
            avgTemp = np.where(radiusGrid == radius, avgGrid[radius], avgTemp)

        # radius < 1 use Intermediate Grid Value
        temp = np.where(np.logical_and(np.less(radiusGrid, 1), np.not_equal(temp, self.noData)), avgTemp, temp)

        # radius > 1.5 average of all neighboring pixels
        kernel = np.ones((3, 3))
        avgAll = ndi.convolve(avgTemp, kernel) / 9

        # radius < 1.5 average of neighbours not on the diagonal
        diagKernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        avgDiag = ndi.convolve(avgTemp, diagKernel) / 5

        dem = np.where(np.logical_and(np.logical_and(np.less(radiusGrid, 1.5), np.greater(temp, 1)), np.not_equal(temp, self.noData)), avgDiag, temp)
        dem = np.where(np.logical_and(np.greater(radiusGrid, 1.5), np.not_equal(temp, self.noData)), avgAll, dem)

        # rescaling back to original value
        dem = np.where(np.not_equal(dem, self.noData), dem / self.par["zFactor"], dem)

        # limit minimum value of smoothening
        dem = np.where(np.less(dem, self.minValue), self.noData, dem)

        return dem

    # generate contour
    def generateContour(self, temp):
        if temp.shape == (2, 2):  # identify tool
            return temp

        temp = self.calculateContourIntermediate(temp)  # calculate intermediate contour values
        topNeighbors = np.roll(temp, 1, axis=0)  # top neighbors of the input pixel block
        rightNeighbors = np.roll(temp, -1, axis=1)  # right neighbors of the input pixel block

        # skip contour generation
        # skip if top, right or center values any one are noData
        # skip if top, right are equal to center values
        nD1 = np.equal(temp, self.noData)
        nD2 = np.logical_or(np.equal(topNeighbors, self.noData), np.equal(rightNeighbors, self.noData))
        nD3 = np.logical_and(np.equal(temp, topNeighbors), np.equal(temp, rightNeighbors))
        skipContour = np.logical_or(np.logical_or(nD1, nD2), nD3)

        # if interval a factor of 2.5 then every 4th contour should be index contour
        if abs(math.floor((math.log10(self.par["interval"] / 2.5) + 3) + 0.5) - (math.log10(self.par["interval"] / 2.5) + 3)) < 0.001:
            self.par["indexContourFactor"] = 4

        dem = np.where(skipContour, self.noData, temp)

        # conditions for contour lines
        # c1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        # c2. hereOutput < topOutput && y > 0 && topOutput >= 0
        # c3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0

        c1 = np.logical_and(np.logical_and(np.greater_equal(temp, topNeighbors), np.greater_equal(temp, rightNeighbors)), np.greater_equal(temp, 0))
        c2 = np.roll(np.logical_and(np.logical_and(np.less(temp, topNeighbors), np.greater_equal(topNeighbors, 0)), np.logical_not(c1)), -1, axis=0)
        c3 = np.roll(np.logical_and(np.logical_and(np.less(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0)), np.logical_not(c1)), 1, axis=1)
        contourLine =  np.logical_or(np.logical_or(c1, c2), c3)

        # set contour lines
        dem = np.where(np.logical_and(contourLine, np.logical_not(skipContour)), 1, dem)

        # index contour lines - darken every 5th contour line
        if self.par["indexContour"]:
            dem = self.generateIndexContour(dem, temp, topNeighbors, rightNeighbors)

        dem[0] = dem[-1] = dem[:, -1] = dem[:, 0] = self.noData  # omitting boundary effects

        return dem

    # generate index contours
    def generateIndexContour(self, dem, temp, topNeighbors, rightNeighbors):
        intTemp = temp.astype('int32')
        intTempPlusOne = (temp + 1).astype('int32')

        # conditions for index contour lines
        # c1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        # c2. hereOutput < topOutput && y > 0 && topOutput >= 0
        # c3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0

        c1 = np.logical_and(np.logical_and(np.logical_and(np.greater_equal(temp, topNeighbors),
             np.greater_equal(temp, rightNeighbors)), np.greater_equal(temp, 0)), np.not_equal(dem, self.noData))
        c2 = np.logical_and(np.logical_and(np.less(temp, topNeighbors), np.greater_equal(topNeighbors, 0)), np.not_equal(dem, self.noData))
        c3 = np.logical_and(np.logical_and(np.less(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0)), np.not_equal(dem, self.noData))

        # c4. <int>(hereOutput) % indexContourFactor == 0
        # c5. <int>(hereOutput +1) % indexContourFactor == 0
        # c6. hereOutput > topOutput
        # c7. hereOutput > rightOutput

        c4 = np.equal(intTemp % self.par["indexContourFactor"], 0)
        c5 = np.equal(intTempPlusOne % self.par["indexContourFactor"], 0)
        c6 = np.logical_and(np.greater(temp, topNeighbors), np.greater_equal(topNeighbors, 0))
        c7 = np.logical_and(np.greater(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0))

        # c8. c1. && c4.
        # c9. c8. && c6. -> top neighbors
        # c10. c8 && c7. -> right neighbors

        c8 = np.logical_and(c1, c4)  # combine c1 & c4
        c9 = np.roll(np.logical_and(c8, c6), -1, axis=0)  # combine c1, c4 & c6
        c10 = np.roll(np.logical_and(c8, c7), 1, axis=1)  # combine c1, c4 & c7

        # release memory
        del c1
        del c4
        del c6
        del c7

        # c11. c2. && c5.
        # c12. c3. && c5.
        # c13. c11. - top neighbors
        # c14. c12. - right neighbors

        c11 = np.logical_and(c2, c5)   # combine c2 & c5
        c12 = np.logical_and(c3, c5)   # combine c3 & c5
        c13 = np.roll(c11, -1, axis=0)
        c14 = np.roll(c12, 1, axis=1)

        combineA = np.logical_or(np.logical_or(c8, c9), c10)
        combineB = np.logical_or(np.logical_or(c11, c12), np.logical_or(c13, c14))

        # set contour lines
        dem = np.where(combineA, 2, dem)
        dem = np.where(combineB, 2, dem)

        return dem

"""
References:
    [1]. Generate contours dynamically with a new raster function
    http://blogs.esri.com/esri/arcgis/2014/09/25/contours_function/

    [2]. Esri (2013): ArcGIS Resources. Contour (Spatial Analyst)
    http://resources.arcgis.com/en/help/main/10.1/index.html#//009z000000ts000000
"""
