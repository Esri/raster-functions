import numpy as np
import math
from scipy import ndimage as ndi


class Contour():

    def __init__(self):
        self.name = "Contour Function"
        self.description = ("Contour Raster Function generates contour lines"
                            "i.e. line joining the points with the same elevation"
                            "from the given DEM raster.")
        self.par = {}  # a dict for input parameters.
        self.noData = None  # store the noData of the input raster.
        self.pixelType = None  # store the pixelType of the input raster.
        self.minimumValue = None  # minimum of the input raster.

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
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
                'description': "Maximum Filter Radius allowed. Limits the amount of smoothing."
            },

        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties':  4 | 8,             # inherit everything except pixelType (1) and noData value (2)
            'invalidateProperties': 2 | 4 | 8,       # invalidate these aspects because we are modifying pixel values and updating key properties.
            'padding': 0,                            # no padding on each of the input pixel block
            'inputMask': True                        # we do need the input mask in .updatePixels()
        }

    def updateRasterInfo(self, **kwargs):
        # set noData value of output raster
        if kwargs['raster_info']['noData'] is None:
            noData = self.assignnoData(kwargs['raster_info']['pixelType'])

        else:
            noData = kwargs['raster_info']['noData']

        # output raster information
        kwargs['output_info']['noData'] = noData
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = kwargs['raster_info']['pixelType']
        kwargs['output_info']['resampling'] = True

        # prepare input parameters
        self.prepare(mode=kwargs.get('mode', 'Contour'),
                     contourChoice=kwargs.get('values', 'No. of Contours'),
                     interval=kwargs.get('interval', 10.0),
                     indexContour=kwargs.get('indexcontour'),
                     base=kwargs.get('base', 0.0),
                     smootheningFactor=kwargs.get('sfactor', 0.6),
                     zFactor=kwargs.get('zfactor', 1.0),
                     slopeRadius=kwargs.get('sloperad', 3.0),
                     averageRadius=kwargs.get('avgrad', 6.0),
                     radiusIncrease=kwargs.get('radinc', 0.0),
                     maxRadius=math.ceil(kwargs.get('maxrad', 6.0)))

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input raster pixel block
        pixels = np.array(pixelBlocks['raster_pixels'], dtype='f8', copy=False)

        # get the input raster mask
        mask = np.array(pixelBlocks['raster_mask'], dtype='u1', copy=False)

        # set raster properties to variables
        self.pixelType = props['pixelType']
        self.noData = props['noData']

        # check if noData value != None
        if self.noData is None:
            self.noData = self.assignnoData(self.pixelType)

        # get minimum value of raster - required for smoothening
        self.minimumValue = self.calculateRasterMinimum(pixels)

        # enable dynamic contouring
        if self.par["contourChoice"] == "No. of Contours":
            self.dynamicContouring(pixels)

        # apply function mode #
        if self.par["mode"] == "Contour":  pixels = self.generateContour(pixels)  # Contour Mode
        elif self.par["mode"] == "Fill":   pixels = self.fillMode(pixels)  # Fill Mode
        else:   pixels = self.smoothRaster(pixels)  # Smoothening Mode

        # output pixel array single band with function mode applied
        pixelBlocks['output_pixels'] = pixels.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = mask.astype('u1', copy=False)

        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.par["mode"]
        return keyMetadata

    # ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
    # other public methods...

    def prepare(self, mode="Contour", contourChoice="No.of Contours", interval=10.0, base=0.0,
                indexContour=True, smootheningFactor=0.6, zFactor=1.0, slopeRadius=3.0,
                averageRadius=6.0, radiusIncrease=0.0, maxRadius=6.0):
        # assign input parameters to dict
        self.par["mode"] = mode
        self.par["contourChoice"] = contourChoice
        self.par["interval"] = interval
        self.par["originalInterval"] =interval
        self.par["base"] = base
        self.par["indexContour"] = indexContour
        self.par["smootheningFactor"] = smootheningFactor
        self.par["zFactor"] = zFactor
        self.par["slopeRadius"] = slopeRadius
        self.par["averageRadius"] = averageRadius
        self.par["radiusIncrease"] = radiusIncrease
        self.par["maxRadius"] = maxRadius

        if indexContour:
            self.par["indexContourFactor"] = 5

        self.par["maximumRadius"] = int(math.ceil(max(max(averageRadius, maxRadius), slopeRadius)))

        # check range of parameters
        if smootheningFactor < 0.1 or smootheningFactor > 10 and (mode != "Contour" and mode != "Fill"):
            raise Exception("Smoothing Factor Out of Range.")

        if mode != "Contour" and mode != "Fill":
            if (slopeRadius < 0.1 or slopeRadius > 5) or (averageRadius < 1 or averageRadius > 10) or (radiusIncrease < 0 or radiusIncrease > 10) or (maxRadius < 5 or maxRadius > 20):
                raise Exception("Check Input Parameters - Out of Range Exception.")

    # assign noData value to output raster
    def assignnoData(self, pixelType):
        # assign noData depending on input pixelType
        if pixelType == 'f4':    noData = np.array([-3.4028235e+038, ])  # float 32 bit
        elif pixelType == 'i4':  noData = np.array([65535, ])  # signed integer 32 bit
        elif pixelType == 'i2':  noData = np.array([32767, ])  # signed integer 16 bit
        elif pixelType == 'i1':  noData = np.array([255, ])  # signed integer 8 bit
        elif pixelType == 'u4':  noData = np.array([-65535, ])  # unsigned integer 32 bit
        elif pixelType == 'u2':  noData = np.array([-32767, ])  # unsigned integer 16 bit
        elif pixelType == 'u1':  noData = np.array([-255, ])  # unsigned integer 8 bit

        return noData

    # get minimum of input pixel block
    def calculateRasterMinimum(self, pixels):
        # mask noData values in raster
        pixels = np.ma.array(pixels, mask=pixels == self.noData)

        # return minimum value in masked input raster
        return np.ma.min(pixels)

    # dynamic contouring - interval calculation #
    def dynamicContouring(self, pixels):
        # mask noData values in raster
        pixels = np.ma.array(pixels, mask=pixels == self.noData)

        stdPixels = np.ma.std(pixels)  # standard deviation of masked input
        maxPixels = np.ma.max(pixels)  # maximum value of masked input
        minPixels = np.ma.min(pixels)  # minimum value of masked input

        range1 = maxPixels - minPixels
        range2 = 5 * stdPixels
        range3 = max(range1, range2)

        cf = mod = m = 0
        cf = math.floor((math.log10(range3 / self.par["originalInterval"]) * 3) + 0.5)
        mod = long(cf % 3)

        if mod == 0:    m = 1
        elif mod == 1:  m = 2
        elif mod == 2:  m = 5

        # new dynamic contour interval
        self.par["interval"] = max(1, m * (10**(math.floor(cf/3))))

    # intermediate contour value #
    def calculateContourIntermediate(self, temp):
        return np.where(temp == self.noData, self.noData, np.floor((temp - self.par["base"])/self.par["interval"]))

    # final contour value #
    def finalContourValue(self, temp):
        return np.where(temp == self.noData, self.noData, (temp * self.par["interval"]) + self.par["base"])

    # fill mode #
    def fillMode(self, temp):
        # calculate intermediate contour values
        intermediateContourValue = self.calculateContourIntermediate(temp)

        # calculate final fill values
        finalFillValue = self.finalContourValue(intermediateContourValue)

        # substitute fill values
        pixels = np.where((finalFillValue - self.par["base"]) <= 0, self.noData, finalFillValue)

        return pixels

    # smooth raster #
    def smoothRaster(self, temp):
        # STEPS FOR SMOOTH RASTER #
        # 1. Initialize Radius Grid
        # 2. Apply Smooth Radius Grid
        # 3. Apply Average Radius Grid
        # 4. Smoothen DEM

        # STEP 1. Initialize Radius Grid #
        radiusGrid = self.initializeGrid(temp)

        # STEP 2. Apply Smooth Radius Grid #
        kernelSlope = self.radiusGridKernel(self.par["slopeRadius"])
        if self.par["slopeRadius"] > 1:
            radiusGrid = ndi.minimum_filter(radiusGrid, footprint=kernelSlope)

        # STEP 3. Apply Average Radius Grid #
        kernelAvg = self.radiusGridKernel(self.par["averageRadius"])
        noOfPixels = len(kernelAvg[kernelAvg == 1])
        if self.par["averageRadius"] > 1:
            radiusGrid = ndi.convolve(radiusGrid, kernelAvg) / noOfPixels

        # STEP 4. Smoothen DEM #
        pixels = self.smoothenDEM(temp, radiusGrid)

        # Apply selected mode for smoothening
        if self.par["mode"] == "Smooth Contour":   pixels = self.generateContour(pixels)
        elif self.par["mode"] == "Smooth Fill":    pixels = self.fillMode(pixels)
        else:                                      pixels = pixels

        return pixels

    # radius grid kernel #
    def radiusGridKernel(self, radius):
        mRadius = int(math.ceil(radius))
        kernel = np.zeros((2 * mRadius + 1, 2 * mRadius + 1))
        y, x = np.ogrid[-mRadius:mRadius + 1, -mRadius:mRadius + 1]
        mask = x**2 + y**2 <= mRadius**2
        kernel[mask] = 1

        return kernel

    # initialize grid for smoothening #
    def initializeGrid(self, temp):
        # applying Z-Factor before any smoothing
        temp = np.where(np.not_equal(temp ,self.noData), temp * self.par["zFactor"], temp)

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

        cond = np.logical_and(np.not_equal(temp, self.noData),np.equal(slopeTangent,0))
        radiusGrid = np.where(cond, self.par["maxRadius"], mTemp)

        # limiting the radius grid between 0 - maximumRadius
        radiusGrid = np.clip(radiusGrid, 0, self.par["maxRadius"])

        return radiusGrid

    # smoothen dem #
    def smoothenDEM(self, temp, radiusGrid):
        maximumRadius = self.par["maximumRadius"] + 1
        radiusGrid = np.floor(radiusGrid).astype(int)
        averageGrid = np.empty((maximumRadius, temp.shape[0], temp.shape[1]))
        averageTemp = np.copy(temp)

        # average neighboring pixels for radius from 0 - maximumRadius
        for grid in xrange(int(maximumRadius)):
            kernel = self.radiusGridKernel(grid)
            noOfPixels = len(kernel[kernel == 1])
            averageGrid[grid] = ndi.convolve(temp, kernel) / noOfPixels

        for radius in xrange(int(maximumRadius)):
            averageTemp = np.where(radiusGrid == radius, averageGrid[radius], averageTemp)

        # radius < 1 use Intermediate Grid Value
        temp = np.where(np.logical_and(np.less(radiusGrid, 1), np.not_equal(temp, self.noData)), averageTemp, temp)

        # radius > 1.5 average of all neighboring pixels
        kernel = np.ones((3, 3))
        averageAllTemp = ndi.convolve(averageTemp, kernel) / 9

        # radius < 1.5 average of neighbours not on the diagonal
        diagKernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        averageDiagTemp = ndi.convolve(averageTemp, diagKernel) / 5

        pixels = np.where(np.logical_and(np.logical_and(np.less(radiusGrid, 1.5), np.greater(temp, 1)), np.not_equal(temp, self.noData)), averageDiagTemp, temp)
        pixels = np.where(np.logical_and(np.greater(radiusGrid, 1.5), np.not_equal(temp, self.noData)) , averageAllTemp, pixels)

        # rescaling back to original value
        pixels = np.where(np.not_equal(pixels, self.noData), pixels / self.par["zFactor"], pixels)

        # limit minimum value of smoothening
        pixels = np.where(np.less(pixels, self.minimumValue), self.noData, pixels)

        return pixels

    # generate contour #
    def generateContour(self, temp):
        # calculate intermediate contour values
        temp = self.calculateContourIntermediate(temp)

        # top neighbors of the input pixel block
        topNeighbors = np.roll(temp, 1, axis=0)

        # right neighbors of the input pixel block
        rightNeighbors = np.roll(temp, -1, axis=1)

        # skip contour generation
        # skip if top, right or center values any one are noData
        # skip if top, right are equal to center values
        noDataPosition = np.logical_or(np.logical_or(np.logical_or(np.equal(temp, self.noData), np.equal(topNeighbors, self.noData)),\
                         np.equal(rightNeighbors, self.noData)), np.logical_and(np.equal(temp, topNeighbors), np.equal(temp, rightNeighbors)))

        # if interval a factor of 2.5 then every 4th contour should be index contour
        if abs(math.floor((math.log10(self.par["interval"] / 2.5) + 3) + 0.5) - (math.log10(self.par["interval"] / 2.5) + 3)) < 0.001:
            self.par["indexContourFactor"] = 4

        pixels = np.where(noDataPosition, self.noData, temp)

        # CONDITIONS FOR CONTOUR LINES #
        # Condition 1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        # Condition 2. hereOutput < topOutput && y > 0 && topOutput >= 0
        # Condition 3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0

        c1 = np.logical_and(np.logical_and(np.greater_equal(temp, topNeighbors), np.greater_equal(temp, rightNeighbors)), np.greater_equal(temp, 0))
        c2 = np.roll(np.logical_and(np.less(temp, topNeighbors), np.greater_equal(topNeighbors, 0)), -1, axis=0)
        c3 = np.roll(np.logical_and(np.less(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0)), 1, axis=1)

        # SET CONTOUR LINES #

        pixels = np.where(np.logical_and(c1, np.not_equal(pixels, self.noData)), 1, pixels)
        pixels = np.where(np.logical_and(c2, np.not_equal(pixels, self.noData)), 1, pixels)
        pixels = np.where(np.logical_and(c3, np.not_equal(pixels, self.noData)), 1, pixels)

        # INDEX CONTOUR LINES - DARKEN EVERY 5th CONTOUR LINE #

        if self.par["indexContour"]:
            pixels = self.generateIndexContour(pixels, temp, topNeighbors, rightNeighbors)

        pixels[0] = pixels[-1] = pixels[:,-1] = pixels[:,0] = self.noData # omitting boundary effects

        return pixels

    # generate index contours
    def generateIndexContour(self, pixels, temp, topNeighbors, rightNeighbors):
        integerTemp = temp.astype('int32')
        integerTempPlusOne = (temp + 1).astype('int32')

        # CONDITIONS FOR INDEX CONTOUR LINES #
        # Condition 1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        # Condition 2. hereOutput < topOutput && y > 0 && topOutput >= 0
        # Condition 3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0

        c1 = np.logical_and(np.logical_and(np.logical_and(np.greater_equal(temp, topNeighbors), np.greater_equal(temp, rightNeighbors)), np.greater_equal(temp, 0)), np.not_equal(pixels, self.noData))
        c2 = np.logical_and(np.logical_and(np.less(temp, topNeighbors), np.greater_equal(topNeighbors, 0)), np.not_equal(pixels, self.noData))
        c3 = np.logical_and(np.logical_and(np.less(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0)), np.not_equal(pixels, self.noData))

        # Condition 4. <int>(hereOutput) % indexContourFactor == 0
        # Condition 5. <int>(hereOutput +1) % indexContourFactor == 0
        # Condition 6. hereOutput > topOutput
        # Condition 7. hereOutput > rightOutput

        c4 = np.equal(integerTemp % self.par["indexContourFactor"], 0)
        c5 = np.equal(integerTempPlusOne % self.par["indexContourFactor"], 0)
        c6 = np.logical_and(np.greater(temp, topNeighbors), np.greater_equal(topNeighbors, 0))
        c7 = np.logical_and(np.greater(temp, rightNeighbors), np.greater_equal(rightNeighbors, 0))

        # Condition 8. Condition 1. && Condition 4.
        # Condition 9. Condition 8. && Condition 6. -> Top Neighbors
        # Condition 10. Condition 8 && Condition 7. -> Right Neighbors

        c8 = np.logical_and(c1, c4)  # Combine c1 & c4
        c9 = np.roll(np.logical_and(c8, c6), -1, axis=0)  # Combine c1, c4 & c6
        c10 = np.roll(np.logical_and(c8, c7), 1, axis=1)  # Combine c1, c4 & c7

        # Condition 11. Condition 2. && Condition 5.
        # Condition 12. Condition 3. && Condition 5.
        # Condition 13. Condition 11. -> Top Neighbors
        # Condition 14. Condition 12. -> Right Neighbors

        c11 = np.logical_and(c2, c5)   # Combine c2 & c5
        c12 = np.logical_and(c3, c5)   # Combine c3 & c5
        c13 = np.roll(c11, -1, axis=0)  # Top Neighbors of c11
        c14 = np.roll(c12, 1, axis=1)  # Right Neighbors of c12

        combinedConditionA = np.logical_or(np.logical_or(c8, c9), c10)
        combinedConditionB = np.logical_or(np.logical_or(c11, c12), np.logical_or(c13, c14))

        # SET CONTOUR LINES #

        pixels = np.where(combinedConditionA, 2, pixels)
        pixels = np.where(combinedConditionB, 2, pixels)

        return pixels


"""
References:
    [1]. Generate contours dynamically with a new raster function
    http://blogs.esri.com/esri/arcgis/2014/09/25/contours_function/
"""
