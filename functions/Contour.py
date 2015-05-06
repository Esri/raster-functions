import numpy as np
from scipy import ndimage as ndi
import math

class Contour():

    def __init__(self):
        self.name = "Contour Function"
        self.description = "Contour Raster Function generates contour lines i.e. line joining the points with the same elevation from the given DEM raster."


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
                'value': 'True',
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
          'inheritProperties':  1 | 2 | 4 |8 ,      # inherit everything
          'invalidateProperties': 2 | 4 | 8,        # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                             # no padding on each of the input pixel block
          'inputMask': True                         # we do need the input mask in .updatePixels()
        }


    def updateRasterInfo(self, **kwargs):
        ### Assignment of parameters ###

        ## contour parameters ##
        self.mode             = kwargs.get('mode','Contour')
        self.contourC         = kwargs.get('values','No. of Contours')
        self.interval         = kwargs.get('interval',10.0)
        self.originalInterval = self.interval
        self.indexC           = kwargs.get('indexcontour','True')
        self.base             = kwargs.get('base',0.0)

        ## smoothing parameters ##
        self.sfactor          = kwargs.get('sfactor',0.6)
        self.zfactor          = kwargs.get('zfactor',1.0)
        self.slopeRad         = kwargs.get('sloperad',3.0)
        self.avgRad           = kwargs.get('avgrad',6.0)
        self.radIncr          = kwargs.get('radinc',0.0)
        self.maxRad           = math.ceil(kwargs.get('maxrad',6.0))

        # if enabled, every 5th contour line is thicker than the rest.
        if self.indexC == "True":
            self.indexContourFactor = 5

        # padding width over input block
        self.maximumRadius = int(math.ceil(max(max(self.avgRad,self.maxRad),self.slopeRad)))

        ### Checking range of parameters ###
        if ((self.sfactor < 0.1 or self.sfactor > 10) and self.mode != "Contour" and self.mode != "Fill"):
            raise Exception("Smoothing Factor Out of Range.")

        if (self.mode != "Contour" and self.mode != "Fill"):
            if (self.slopeRad < 0.1 or self.slopeRad > 5) \
            or (self.avgRad < 1 or self.avgRad > 10) \
            or (self.radIncr < 0 or self.radIncr > 10) \
            or (self.maxRad < 5 or self.maxRad > 20):
                raise Exception("Check Input Parameters - Out of Range Exception.")

        # noData computation


        # output information
        if str(kwargs['raster_info']['pixelType']) =='f4':
            kwargs['output_info']['noData'] = np.array([-3.40282346639e+038])
        elif str(kwargs['raster_info']['pixelType']) =='i4':
            kwargs['output_info']['noData'] = np.array([65535])
        elif str(kwargs['raster_info']['pixelType']) =='i2':
            kwargs['output_info']['noData'] = np.array([32767])
        elif str(kwargs['raster_info']['pixelType']) =='i1':
            kwargs['output_info']['noData'] = np.array([255])
        elif str(kwargs['raster_info']['pixelType']) =='u4':
            kwargs['output_info']['noData'] = np.array([-65535])
        elif str(kwargs['raster_info']['pixelType']) =='u2':
            kwargs['output_info']['noData'] = np.array([-32767])
        elif str(kwargs['raster_info']['pixelType']) =='u1':
            kwargs['output_info']['noData'] = np.array([-255])

        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = kwargs['raster_info']['pixelType']
        kwargs['output_info']['resampling'] = True
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()


        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        r = np.array(pixelBlocks['raster_pixels'], dtype = props['pixelType'], copy=False)
        m = np.array(pixelBlocks['raster_mask'], dtype = 'u1',copy=False)
        self.noData = props['noData']
        self.pixelType = props['pixelType']

        # enable dynamic contouring
        if self.contourC == "No. of Contours":
            self.dynamicContouring(r)

        # apply selected mode
        if self.mode == "Contour":
            r = self.generateContour(r)

        elif self.mode == "Smooth Contour":
            r = self.smoothRaster(r)
            r = self.generateContour(r)

        elif self.mode == "Fill":
            r = self.fillMode(r)

        elif self.mode == "Smooth Fill":
            r = self.smoothRaster(r)
            r = self.fillMode(r)

        else:
            r = self.smoothRaster(r)

        pixelBlocks['output_pixels'] = r.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask']   = m.astype('u1',copy = False)

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Contour'
        return keyMetadata

    def dynamicContouring(self,r):
        # mask noData values in raster
        r = np.ma.array(r, mask= r == self.noData)

        # dynamic interval calculation
        stdR  = np.ma.std(r)
        maxR  = np.ma.max(r)
        minR  = np.ma.min(r)

        range1 = maxR - minR
        range2 = 5 * stdR
        range3 = max(range1,range2)

        cf = mod = m = 0
        cf  = math.floor((math.log10(range3/self.originalInterval)*3)+0.5)
        mod = long (cf % 3)

        if mod == 0:    m=1
        elif mod == 1:  m=2
        elif mod == 2:  m=5

        self.interval = max(1 , m * (10**(math.floor(cf/3))))


    def calculateContourIntermediate(self,r):
        temp =  np.where(r == self.noData, self.noData , np.floor((r - self.base)/self.interval))
        return temp

    def finalContourValue(self,temp):
        temp = np.where(temp == self.noData, self.noData, (temp * self.interval) + self.base)
        return temp

    def fillMode(self,r):
        temp  = self.calculateContourIntermediate(r)    # calculate intermediate contour values
        temp  = self.finalContourValue(temp)            # calculate final contour values
        r     = np.where((temp-self.base) <= 0 , self.noData , temp)
        return r

    def generateContour(self,r):
        temp     = self.calculateContourIntermediate(r)
        rTop     = np.roll(temp, 1, axis=0)         # top neighbours
        rRight   = np.roll(temp, -1, axis=1)        # right neighbours

        noDataPos = np.logical_or(np.logical_or(np.logical_or(np.equal(temp,self.noData),np.equal(rTop,self.noData)),\
                    np.equal(rRight,self.noData)),np.logical_and(np.equal(temp,rTop) ,np.equal(temp,rRight)))         # conditions to omit contour calculation

        # if interval a factor of 2.5 then every 4th contour should be index contour
        if (abs(math.floor((math.log10(self.interval/2.5)+3)+ 0.5) - ( math.log10(self.interval/2.5)+3 )) < 0.001):
            self.indexContourFactor = 4

        r = np.where(noDataPos,self.noData,temp)

        ## condition 1. hereOutput >= topOutput && hereOutput >= rightOutput  && hereOutput >=0
        condition1 = np.logical_and(np.logical_and(np.greater_equal(temp,rTop),np.greater_equal(temp,rRight)),np.greater_equal(temp,0))

        ## condtion 2. hereOutput < topOutput && y > 0 && topOutput >= 0
        condition2 = np.logical_and(np.less(temp,rTop),np.greater_equal(rTop,0))
        condition2 = np.roll(condition2, -1,axis = 0)

        ## condtion 3. hereOutput < rightOutput && x < width - 1 && rightOutput >= 0
        condition3 = np.logical_and(np.less(temp,rRight),np.greater_equal(rRight,0))
        condition3 = np.roll(condition3, 1,axis = 1)


        finalOutput = self.finalContourValue(temp)
        # Set contour lines
        r = np.where(np.logical_and(condition1,np.not_equal(r,self.noData)),finalOutput,r)
        r = np.where(np.logical_and(condition2,np.not_equal(r,self.noData)),finalOutput,r)
        r = np.where(np.logical_and(condition3,np.not_equal(r,self.noData)),finalOutput,r)

        # index contour lines
        if self.indexC == "True":
            tempInt1 = temp.astype(int)
            tempInt2 = (temp + 1).astype(int)

            ## condition 4. <int>(hereOutput ) % indexContourFactor == 0
            condition4 = np.equal(tempInt1 % self.indexContourFactor , 0)

            ## condition 5. <int>(hereOutput +1) % indexContourFactor == 0
            condition5 = np.equal(tempInt2 % self.indexContourFactor , 0)

            ## condition 6. hereOutput > topOutput
            condition6 = np.greater(temp,rTop)

            ## condition 7. hereOutput > rightOutput
            condition7 = np.greater(temp,rRight)

            condition8 = np.logical_and(np.logical_and(condition1,condition4),condition6)
            condition8 = np.roll(condition8, -1,axis = 0)
            r = np.where(condition8 ,finalOutput,r)

            condition9 = np.logical_and(np.logical_and(condition1,condition4),condition7)
            condition9 = np.roll(condition9, 1,axis = 1)
            r = np.where(condition9 ,finalOutput,r)

            condition10 = np.logical_and(np.logical_not(condition1),condition5)
            r = np.where(condition10 ,finalOutput,r)


        ## dynamic contouring scale to 8 bit
        if self.mode == "Smooth Contour":
            r = np.ma.array(r, mask= r == self.noData)
            maxR  = np.ma.max(r)
            minR  = np.ma.min(r)
            r =  np.array((((r - minR) / (maxR - minR)) * 255.)).astype(self.pixelType)

        # omitting boundary effects
        r[0] = r[-1] = r[:,-1] = r[:,0] = self.noData

        return r


    def smoothRaster(self,r):
        # initialize the grid
        radGrid = self.initializeGrid(r)

        # Smooth Radius and Average Radius Operations
        m_SlopeRad = int(math.ceil(self.slopeRad))
        m_AvgRad = int(math.ceil(self.avgRad))

        kernelSlope = np.zeros((2*m_SlopeRad+1, 2*m_SlopeRad+1))
        y,x = np.ogrid[-m_SlopeRad:m_SlopeRad+1, -m_SlopeRad:m_SlopeRad+1]
        mask = x**2 + y**2 <= m_SlopeRad**2
        kernelSlope[mask] = 1

        kernelAvg = np.zeros((2*m_AvgRad+1, 2*m_AvgRad+1))
        y,x = np.ogrid[-m_AvgRad:m_AvgRad+1, -m_AvgRad:m_AvgRad+1]
        mask = x**2 + y**2 <= m_AvgRad**2
        kernelAvg[mask] = 1
        noOfPixels = len(kernelAvg[kernelAvg==1])

        # smooth & average radius grid
        if self.slopeRad > 1:
           radGrid = ndi.minimum_filter(radGrid, footprint=kernelSlope)

        if self.avgRad > 1:
           radGrid = ndi.convolve(radGrid, kernelAvg) / noOfPixels

        # smooth dem
        r = self.smoothenDEM(r,radGrid)

        return r

    def initializeGrid(self,r):
        # applying z-factor before smoothing
        r = np.where(np.not_equal(r ,self.noData), r * self.zfactor, r)

        # obtaining the slope of each pixel within the block
        xKernel = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
        yKernel = np.array([[-1,-2,-1],[0,0,0],[1,2,1]])

        deltaX = ndi.convolve(r, xKernel)
        deltaY = ndi.convolve(r, yKernel)

        slopeTangent = np.sqrt(deltaX * deltaX + deltaY * deltaY) / 8

        # final else condition in kernel manipulation
        rGRTemp = self.interval * self.sfactor / slopeTangent + self.radIncr

        # assigning the radius grid to each pixel
        condition1 = np.equal(r,self.noData)
        rGR = np.where(condition1, self.maxRad, r)

        condition2 = np.logical_and(np.not_equal(r,self.noData),np.equal(slopeTangent,0))
        rGR = np.where(condition2,self.maxRad, rGRTemp)

        # limiting the radius grid between 0 - maximumRadius
        rGR = np.clip(rGR,0,self.maxRad)

        return rGR


    def smoothenDEM(self, r, radGrid):
        radGrid = np.floor(radGrid).astype(int)
        rTempAvg = np.empty((self.maximumRadius+1,r.shape[0],r.shape[1]))
        outputR = np.copy(r)

        # average neighboring pixels for radius from 0 - maximumRadius
        for z in xrange(int(self.maximumRadius+1)):
            kernel= np.zeros((2*z+1, 2*z+1))
            y,x = np.ogrid[-z:z+1, -z:z+1]
            mask = x**2 + y**2 <= z**2
            kernel[mask] = 1
            noOfPixels = len(kernel[kernel==1])
            rTempAvg[x] = ndi.convolve(r, kernel) / noOfPixels

        for x in xrange(int(self.maximumRadius+1)):
            outputR = np.where(radGrid == x, rTempAvg[x],outputR)

        # radius < 1 use Intermediate Grid Value
        r = np.where(np.logical_and(np.less(radGrid,1),np.not_equal(r,self.noData)),outputR,r)

        # radius > 1.5 average of all neighboring pixels
        kernel = np.ones((3,3))
        outputRAvgAll = ndi.convolve(outputR,kernel) / 9

        # radius < 1.5 average of neighbours not on the diagonal
        diagKernel = np.array([[0,1,0],[1,1,1],[0,1,0]])
        outputRAvgDiag = ndi.convolve(outputR,diagKernel) / 5

        r = np.where(np.logical_and(np.logical_and(np.less(radGrid,1.5),np.greater(r,1)),np.not_equal(r,self.noData)),outputRAvgDiag,r)
        r = np.where(np.logical_and(np.greater(radGrid, 1.5),np.not_equal(r,self.noData)) , outputRAvgAll,r)

        # rescaling back to original value
        r = np.where(np.not_equal(r,self.noData),r/self.zfactor,r)
        return r

