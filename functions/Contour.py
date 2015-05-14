import numpy as np
from scipy import ndimage as ndi
import math
import utils

class Contour():

    def __init__(self):
        self.name = "Contour Function"
        self.description = "Contour Raster Function generates contour lines i.e. line joining the points with the same elevation from the given DEM raster."
        self.trace = utils.Trace()

    def getParameterInfo(self):
        return [
             {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ("A DEM Raster where each pixel stores the elevation of a particular point.")
            },
            {
                'name': 'mode',
                'dataType': 'string',
                'value': 'Contour',
                'required': True,
                'domain': ('Contour','Smooth Contour','Fill','Smooth Fill','Smoothing Only'),
                'displayName': "Mode",
                'description': "Select Mode for Contour Function."
            },
            {
                'name': 'values',
                'dataType': 'string',
                'value': 'No. of Contours',
                'required': True,
                'domain': ('No. of Contours','Contour Interval'),
                'displayName': "Draw",
                'description':("No.of Contour : Signifies the average number of contour lines the user wants to see. or "
                               "Contour Interval : To specify the difference in elevation between two consecutive.")
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
                'dataType': 'string',
                'value': 'False',
                'required': True,
                'domain': ('True','False'),
                'displayName': "Index Contour",
                'description': "If enabled, every 5th contour line is thicker than the rest."
            },
            {
                'name': 'sfactor',
                'dataType': 'numeric',
                'value': 0.6,
                'required': True,
                'displayName': "Smoothing Factor",
                'description': "Defines how much smoothing to apply. Higher the value, more the smoothing"
            },
            {
                'name': 'zfactor',
                'dataType': 'numeric',
                'value': 1.0,
                'required': True,
                'displayName': "Z-Factor",
                'description': "Z-Factor for Advanced Smoothing"
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
                'description': "Maximum Filter Radius allowed. Limits the amount of smoothing.."
            },

        ]


    def getConfiguration(self, **scalars):
        return {
          'inheritProperties':  4 | 8 ,             # inherit everything except pixelType (1) and noData value (2)
          'invalidateProperties': 2 | 4 | 8,        # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                             # no padding on each of the input pixel block
          'inputMask': True                         # we do need the input mask in .updatePixels()
        }


    def updateRasterInfo(self, **kwargs):
        ### Assignment of parameters ###

        ## contour parameters ##
        self.mode             = kwargs.get('mode','Contour')
        self.contourChoice    = kwargs.get('values','No. of Contours')
        self.interval         = kwargs.get('interval',10.0)
        self.originalInterval = self.interval
        self.indexC           = kwargs.get('indexcontour','False')
        self.base             = kwargs.get('base',0.0)

        ## smoothing parameters ##
        self.sfactor          = kwargs.get('sfactor',0.6)
        self.zfactor          = kwargs.get('zfactor',1.0)
        self.slopeRad         = kwargs.get('sloperad',3.0)
        self.avgRad           = kwargs.get('avgrad',6.0)
        self.radIncr          = kwargs.get('radinc',0.0)
        self.maxRad           = math.ceil(kwargs.get('maxrad',6.0))

        if self.indexC == "True":  self.indexContourFactor = 5 # if enabled, every 5th contour line is thicker than the rest.

        self.maximumRadius = int(math.ceil(max(max(self.avgRad,self.maxRad),self.slopeRad))) # padding width over input block

        ### Checking range of parameters ###
        if ((self.sfactor < 0.1 or self.sfactor > 10) and self.mode != "Contour" and self.mode != "Fill"):
            raise Exception("Smoothing Factor Out of Range.")

        if (self.mode != "Contour" and self.mode != "Fill"):
            if (self.slopeRad < 0.1 or self.slopeRad > 5) \
            or (self.avgRad < 1 or self.avgRad > 10) \
            or (self.radIncr < 0 or self.radIncr > 10) \
            or (self.maxRad < 5 or self.maxRad > 20):
                raise Exception("Check Input Parameters - Out of Range Exception.")

        # output information
        inputnoData                         = kwargs['raster_info']['noData']
        kwargs['output_info']['noData']     = self.assignNoData(kwargs['raster_info']['pixelType']) if inputnoData == None else inputnoData
        kwargs['output_info']['bandCount']  = 1
        kwargs['output_info']['pixelType']  = kwargs['raster_info']['pixelType']
        kwargs['output_info']['resampling'] = True

        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r = np.array(pixelBlocks['raster_pixels'], dtype = props['pixelType'], copy=False)
        m = np.array(pixelBlocks['raster_mask'], dtype = 'u1',copy=False)

        self.pixelType, self.noData = props['pixelType'] , props['noData'] # raster properties
        if self.noData  == None: self.noData = self.assignNoData(self.pixelType)

        if self.contourChoice == "No. of Contours":  self.dynamicContouring(r)  # enable dynamic contouring

        ## APPLY CONTOUR MODE ##
        if   self.mode == "Contour":         r = self.generateContour(r)
        elif self.mode == "Smooth Contour":  r = self.smoothRaster(r)
        elif self.mode == "Fill":            r = self.fillMode(r)
        elif self.mode == "Smooth Fill":     r = self.smoothRaster(r)
        else:                                r = self.smoothRaster(r)

        pixelBlocks['output_pixels'] = r.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask']   = m.astype('u1',copy = False)

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = self.mode
        return keyMetadata

    # assign noData value
    def assignNoData(self, pixelType):
        if   pixelType =='f4':   noData = np.array([-3.4028235e+038])
        elif pixelType =='i4':   noData = np.array([65535])
        elif pixelType =='i2':   noData = np.array([32767])
        elif pixelType =='i1':   noData = np.array([255])
        elif pixelType =='u4':   noData = np.array([-65535])
        elif pixelType =='u2':   noData = np.array([-32767])
        elif pixelType =='u1':   noData = np.array([-255])

        return noData

    ## DYNAMIC CONTOURING - INTERVAL CALCULATION ##
    def dynamicContouring(self,r):

        r = np.ma.array(r, mask= r == self.noData) # mask noData values in raster

        stdR  = np.ma.std(r)    # standard deviation
        maxR  = np.ma.max(r)    # maximum value
        minR  = np.ma.min(r)    # minimum value

        range1 = maxR - minR
        range2 = 5 * stdR
        range3 = max(range1,range2)

        cf  = mod = m = 0
        cf  = math.floor((math.log10(range3/self.originalInterval)*3)+0.5)
        mod = long (cf % 3)

        if   mod == 0:  m=1
        elif mod == 1:  m=2
        elif mod == 2:  m=5

        self.interval = max(1 , m * (10**(math.floor(cf/3)))) # new dynamic contour line

    ## INTERMEDIATE CONTOUR VALUE ##
    def calculateContourIntermediate(self, temp):
        intermediateContourValue =  np.where(temp == self.noData, self.noData , np.floor((temp - self.base)/self.interval))

        return intermediateContourValue

    ## FINAL CONTOUR VALUE ##
    def finalContourValue(self, temp):
        finalContourValue        = np.where(temp == self.noData, self.noData, (temp * self.interval) + self.base)

        return finalContourValue

    ## FILL MODE ##
    def fillMode(self, temp):
        intermediateContourValue  = self.calculateContourIntermediate(temp)             # calculate intermediate contour values
        finalFillValue            = self.finalContourValue(intermediateContourValue) # calculate final contour values
        r                         = np.where((finalFillValue - self.base) <= 0 , self.noData , finalFillValue)

        # release memory
        del intermediateContourValue
        del finalFillValue

        return r

    ## GENERATE CONTOUR ##
    def generateContour(self, temp):

        temp             = self.calculateContourIntermediate(temp)  # calculate contour intermediate values
        topNeighbors     = np.roll(temp, 1, axis=0)                 # top neighbours
        rightNeighbors   = np.roll(temp, -1, axis=1)                # right neighbours

        # conditions to omit contour calculation
        noDataPos = np.logical_or(np.logical_or(np.logical_or(np.equal(temp, self.noData),np.equal(topNeighbors, self.noData)),\
                    np.equal(rightNeighbors,self.noData)), np.logical_and(np.equal(temp,topNeighbors), np.equal(temp,rightNeighbors)))

        # if interval a factor of 2.5 then every 4th contour should be index contour
        if (abs(math.floor((math.log10(self.interval / 2.5) +3) + 0.5) - (math.log10(self.interval / 2.5) +3)) < 0.001):  self.indexContourFactor = 4

        r = np.where(noDataPos, self.noData, temp)

        ####### CONDITIONS FOR CONTOUR LINES #######

        # Condition 1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        # Condition 2. hereOutput < topOutput && y > 0 && topOutput >= 0
        # Condition 3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0

        c1 = np.logical_and(np.logical_and(np.greater_equal(temp, topNeighbors), np.greater_equal(temp, rightNeighbors)), np.greater_equal(temp,0))
        c2 = np.roll(np.logical_and(np.less(temp, topNeighbors),np.greater_equal(topNeighbors, 0)), -1, axis = 0)
        c3 = np.roll(np.logical_and(np.less(temp, rightNeighbors),np.greater_equal(rightNeighbors, 0)), 1, axis = 1)

        finalContourValue = self.finalContourValue(temp)

        ####### SET CONTOUR LINES #######

        r = np.where(np.logical_and(c1, np.not_equal(r,self.noData)), finalContourValue, r)
        r = np.where(np.logical_and(c2, np.not_equal(r,self.noData)), finalContourValue, r)
        r = np.where(np.logical_and(c3, np.not_equal(r,self.noData)), finalContourValue, r)

        ####### INDEX CONTOUR LINES - DARKEN EVERY 5th CONTOUR LINE #######

        if self.indexC == "True":

            intTemp       = temp.astype(int)
            intTempIncBy1 = (temp + 1).astype(int)

            ####### CONDITIONS FOR INDEX CONTOUR LINES #######

            # Condition 4. <int>(hereOutput) % indexContourFactor == 0
            # Condition 5. <int>(hereOutput +1) % indexContourFactor == 0
            # Condition 6. hereOutput > topOutput
            # Condition 7. hereOutput > rightOutput

            c4 = np.equal(intTemp % self.indexContourFactor , 0)
            c5 = np.equal(intTempIncBy1 % self.indexContourFactor , 0)
            c6 = np.greater(temp, topNeighbors)
            c7 = np.greater(temp, rightNeighbors)

            c_146 = np.roll(np.logical_and(np.logical_and(c1, c4), c6), -1, axis = 0)  # Combine c1 & c4 & c6
            c_147 = np.roll(np.logical_and(np.logical_and(c1, c4), c7), 1, axis = 1)   # Combine c1 & c4 & c7
            c_15  = np.logical_and(np.logical_not(c1), c5) # Combine c1 & c5

            ####### SET INDEX CONTOUR LINES #######

            r = np.where(c_146, finalContourValue * 2, r)
            r = np.where(c_147, finalContourValue * 2, r)
            r = np.where(c_15, finalContourValue * 2, r)

        if self.mode == "Smooth Contour":   r = self.dynamicScaling(r) # dynamic contouring scale to 8 bit

        r[0] = r[-1] = r[:,-1] = r[:,0] = self.noData # omitting boundary effects

        return r

    ## DYNAMIC SCALING - FOR SMOOTH CONTOUR ##
    def dynamicScaling(self, temp):

        temp       = np.ma.array(temp, mask= temp == self.noData)
        maxR       = np.ma.max(temp)
        minR       = np.ma.min(temp)
        scaledTemp = np.array((((temp - minR) / (maxR - minR)) * 255.)).astype(self.pixelType)

        return scaledTemp

    ## SMOOTH RASTER ##
    def smoothRaster(self, temp):

        ####### STEPS FOR SMOOTH RASTER #######

        # 1. Initialize Radius Grid
        # 2. Apply Smooth Radius Grid
        # 3. Apply Average Radius Grid
        # 4. Smoothen DEM

        ####### STEP 1. INITIALIZE RADIUS GRID #######

        radGrid = self.initializeGrid(temp)

        ####### STEP 2. APPLY SMOOTH RADIUS GRID #######

        m_SlopeRad   = int(math.ceil(self.slopeRad))
        kernelSlope  = np.zeros((2 * m_SlopeRad + 1, 2 * m_SlopeRad + 1))
        y , x          = np.ogrid[-m_SlopeRad:m_SlopeRad+1, -m_SlopeRad:m_SlopeRad+1]
        mask         = x**2 + y**2 <= m_SlopeRad**2
        kernelSlope[mask] = 1

        if self.slopeRad > 1:    radGrid = ndi.minimum_filter(radGrid, footprint=kernelSlope)

        ####### STEP 3. APPLY AVERAGE RADIUS GRID #######

        m_AvgRad     = int(math.ceil(self.avgRad))
        kernelAvg    = np.zeros((2 * m_AvgRad + 1, 2 * m_AvgRad + 1))
        y , x        = np.ogrid[-m_AvgRad:m_AvgRad+1, -m_AvgRad:m_AvgRad+1]
        mask         = x**2 + y**2 <= m_AvgRad**2
        kernelAvg[mask] = 1
        noOfPixels   = len(kernelAvg[kernelAvg == 1])

        if self.avgRad > 1:      radGrid = ndi.convolve(radGrid, kernelAvg) / noOfPixels

        ####### STEP 4. SMOOTHEN DEM #######

        r = self.smoothenDEM(temp, radGrid)

        if self.mode == "Smooth Contour":   r = self.generateContour(r)
        elif self.mode == "Smooth Fill":    r = self.fillMode(r)
        else:                               r = r


        return r

    ## INITIALIZE GRID FOR SMOOTHENING ##
    def initializeGrid(self, temp):

        temp    = np.where(np.not_equal(temp ,self.noData), temp * self.zfactor, temp) # applying Z-Factor before any Smoothing

        # obtaining the slope of each pixel within the block
        xKernel = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
        yKernel = np.array([[-1,-2,-1],[0,0,0],[1,2,1]])

        deltaX  = ndi.convolve(temp, xKernel)
        deltaY  = ndi.convolve(temp, yKernel)

        slopeTangent = np.sqrt(deltaX * deltaX + deltaY * deltaY) / 8

        m_temp  = self.interval * self.sfactor / slopeTangent + self.radIncr # final assignment value

        temp    = np.where(np.equal(temp, self.noData), self.maxRad, temp) # assigning the radius grid to each pixel

        cond    = np.logical_and(np.not_equal(temp, self.noData),np.equal(slopeTangent,0))
        radGrid = np.where(cond, self.maxRad, m_temp)
        radGrid = np.clip(radGrid, 0, self.maxRad)  # limiting the radius grid between 0 - maximumRadius

        return radGrid


    ## SMOOTHEN DEM ##
    def smoothenDEM(self, temp, radGrid):

        radGrid  = np.floor(radGrid).astype(int)
        avg_temp = np.empty((self.maximumRadius+1, temp.shape[0], temp.shape[1]))
        r_temp   = np.copy(temp)

        # average neighboring pixels for radius from 0 - maximumRadius
        for grid in xrange(int(self.maximumRadius+1)):
            kernel  = np.zeros((2 * grid + 1, 2 * grid + 1))
            y,x     = np.ogrid[-grid:grid+1, -grid:grid+1]
            mask    = x**2 + y**2 <= grid**2
            kernel[mask] = 1
            noOfPixels   = len(kernel[kernel==1])
            avg_temp[grid] = ndi.convolve(temp, kernel) / noOfPixels

        for radius in xrange(int(self.maximumRadius + 1)):
            r_temp = np.where(radGrid == radius, avg_temp[radius], r_temp)

        # radius < 1 use Intermediate Grid Value
        temp = np.where(np.logical_and(np.less(radGrid, 1), np.not_equal(temp, self.noData)), r_temp, temp)

        # radius > 1.5 average of all neighboring pixels
        kernel      = np.ones((3,3))
        avgAll_temp = ndi.convolve(r_temp, kernel) / 9

        # radius < 1.5 average of neighbours not on the diagonal
        diagKernel   = np.array([[0,1,0],[1,1,1],[0,1,0]])
        avgDiag_temp = ndi.convolve(r_temp, diagKernel) / 5

        r = np.where(np.logical_and(np.logical_and(np.less(radGrid, 1.5), np.greater(temp, 1)), np.not_equal(temp, self.noData)), avgDiag_temp, temp)
        r = np.where(np.logical_and(np.greater(radGrid, 1.5), np.not_equal(temp, self.noData)) , avgAll_temp, r)

        r = np.where(np.not_equal(r,self.noData), r / self.zfactor, r) # rescaling back to original value

        return r

