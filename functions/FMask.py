import numpy as np
import scipy as sp
import math
from skimage import morphology, measure, segmentation


class FMask():

    def __init__(self):
        self.name = "FMask Function"
        self.description = ("Used for cloud & cloud shadow detection"
                            "in Landsat imagery")

    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Top of Atmosphere Reflectances",
                'description': ("TOA Reflectance values multispectral bands.")
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Thermal Band",
                'description': ("Thermal band of Landsat scene. (Landsat 8: Band 10, Landsat 5-7: Band 6)")
            },
            {
                'name': 'mode',
                'dataType': 'string',
                'value': 'Mask Cloud',
                'required': True,
                'domain': ('Mask Cloud', 'Mask Cloud & Cloud Shadow',
                           'Mask Snow', 'Mask Cloud, Cloud Shadow & Snow'),
                'displayName': "Masking Feature",
                'description': "Select masking feature for Landsat Scene"
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,                                   # inherit everything but the pixel type (1) and no Data (2)
          'invalidateProperties': 2 | 4 | 8,                            # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                                                 # no padding on each of the input pixel block
          'inputMask': False,                                           # we don't need the input mask in .updatePixels()
          'keyMetadata': ('sensorname', 'sunazimuth', 'sunelevation'),  # key property used in cloud shadow detection
        }

    def updateRasterInfo(self, **kwargs):
        # get masking feature
        self.mode = kwargs['mode']

        # get key metadata from input raster
        # used for cloud shadow detection
        self.sunElevation = kwargs['r1_keyMetadata'].get("sunelevation")
        self.sunAzimuth = kwargs['r1_keyMetadata'].get("sunazimuth")
        self.scene = kwargs['r1_keyMetadata'].get('sensorname')

        # get resolution of the input raster
        # used for calculating steps of iterations in cloud shadow detection
        self.cellSize = kwargs['r1_info']['cellSize']

        # output raster information
        kwargs['output_info']['bandCount'] = kwargs['r1_info']['bandCount']
        kwargs['output_info']['pixelType'] = kwargs['r1_info']['pixelType']
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['noData'] = np.array([0, ])
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get input TOA reflectance multispectral bands
        pixels = np.array(pixelBlocks['r1_pixels'], dtype='f4')

        # get input thermal band of landsat scene
        thermalBand = np.array(pixelBlocks['r2_pixels'], dtype='f4')

        # convert thermal band values to brightness temperature
        # get bandIDs depending on landsat scene
        thermalBand, bandId = self.convertThermalBand(thermalBand)

        # perform masking operation
        ptm, temp, tempLow, tempHigh, water, snow, cloud, shadow, dim = self.potentialCloudShadowSnowMask(pixels, thermalBand, bandId)

        # object matching & dilation of mask
        fmask = self.objectCloudShadowMatch(ptm, temp, tempLow, tempHigh, water, snow, cloud, shadow, dim)

        # replace masking feature with noData value
        for band in xrange(pixels.shape[0]):
            pixels[band] = np.where(fmask, 0, pixels[band])

        # output pixel arrays of multispectral bands with masked features
        pixelBlocks['output_pixels'] = pixels.astype('f4')
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

    def convertThermalBand(self, thermalBand):
        # assign properties depending on sensor name
        if self.scene == "Landsat 8":
            k1 = 774.89      # thermal conversion constant K1
            k2 = 1321.08     # thermal conversion constant K2
            lmax = 22.00180  # thermal band MAX_RADIANCE
            lmin = 0.10033   # thermal band MIN_RADIANCE
            dn = 65534       # digital number limit
            bandId = [1, 2, 3, 4, 5, 6, 7]  # band IDs

        elif self.scene == "Landsat 7":
            k1 = 666.09
            k2 = 1282.71
            lmax = 17.04
            lmin = 0.0
            dn = 244
            bandId = [0, 1, 2, 3, 4, 5]

        else:
            k1 = 607.76
            k2 = 1260.56
            lmax = 15.303
            lmin = 1.238
            dn = 244
            bandId = [0, 1, 2, 3, 4, 5]

        # convert thermal band value to brightness temperature
        thermalBand = ((lmax - lmin)/dn) * thermalBand + lmin

        # calculate deg. celsius difference
        thermalBand = 100 * (((k2/np.log((k1/thermalBand)+1))) - 273.15)

        return thermalBand, bandId

    # Identify the cloud pixels, snow pixels, water pixels,
    # clear land pixels, and potential shadow pixels
    def potentialCloudShadowSnowMask(self, pixels, thermalBand, bandId):
        # dimensions of scene
        dim = pixels[0].shape

        # cirrus band probability for landsat 8
        if self.scene != "Landsat 8":
            thinProb = 0
        else:
            thinProb = (10**4) * pixels[-1] / 400

        cloud = np.zeros(dim, 'uint8')   # Cloud mask
        snow = np.zeros(dim, 'uint8')    # Snow mask
        water = np.zeros(dim, 'uint8')   # Water mask
        shadow = np.zeros(dim, 'uint8')  # Shadow mask

        # assignment of Landsat bands to temporary variables
        mulFactor = (10**4)
        data1 = mulFactor * pixels[bandId[0]]
        data2 = mulFactor * pixels[bandId[1]]
        data3 = mulFactor * pixels[bandId[2]]
        data4 = mulFactor * pixels[bandId[3]]
        data5 = mulFactor * pixels[bandId[4]]
        data6 = mulFactor * pixels[bandId[5]]

        # assignment of thermal band to temporary variable
        temp = thermalBand

        # calculate NDSI
        NDSI = self.calculateNDSI(pixels, bandId)

        # calculate NDVI
        NDVI = self.calculateNDVI(pixels, bandId)

        # release memory
        del pixels
        del thermalBand

        # overlapping region of thermal band and multispectral bands
        mask = np.greater(temp, -9999)

        # saturation test for visible bands B1, B2 & B3
        satuBands = np.logical_or(np.less(data1, 0), np.logical_or(np.less(data2, 0), np.less(data3, 0)))

        # PASS 1 #
        # POTENTIAL CLOUD PIXELS #
        # perform multiple spectral tests to obtain potential cloud pixels

        # basic test
        # condition : Band 7 > 0:03 and BT < 27 and NDSI < 0.8 and NDVI < 0.8
        pCloudPixels = np.logical_and(np.logical_and(np.less(NDSI, 0.8), np.less(NDVI, 0.8)),
                                      np.logical_and(np.greater(data6, 300), np.less(temp, 2700)))

        # snow test
        # condition: NDSI > 0.15 and BT < 3.8 and Band4 > 0.11 and Band 2 > 0.1
        # OR condition used to include all pixels between thin / thick clouds
        snowCondition = np.logical_or(np.logical_and(np.greater(NDSI, 0.15), np.logical_and(np.greater(data4, 1100),
                                      np.greater(data2, 1000))), np.less(temp, 400))

        # mask snow in array
        snow[snowCondition] = 1
        snow[mask == 0] = 255

        # water test
        # condition : (NDVI < 0.01 and Band4 < 0.11) or (NDVI < 0.1 and NDVI > 0 and Band4 < 0.05)
        waterCondition = np.logical_or(np.logical_and(np.less(NDVI, 0.01), np.less(data4, 1100)),
                                       np.logical_and(np.logical_and(np.less(NDVI, 0.1), np.greater(NDVI, 0)),
                                       np.less(data4, 500)))

        # mask water in array
        water[waterCondition] = 1
        water[mask == 0] = 255

        # whiteness test
        # condition : (Sum(Band (1, 2, 3) - mean)/ mean) < 0.7
        # mean of visible bands B1, B2 & B3
        visiMean = (data1 + data2 + data3)/3
        whiteness = (np.abs(data1 - visiMean) + np.abs(data2 - visiMean) + np.abs(data3 - visiMean)) / visiMean
        whiteness[satuBands] = 0

        # release memory
        del visiMean

        # update potential cloud pixels
        pCloudPixels = np.logical_and(pCloudPixels, np.less(whiteness, 0.7))

        # hot (haze optimized transformation) test
        # condition : Band1 - 0.5 * Band3 - 0.08 > 0
        hot = (np.logical_or(np.greater((data1 - 0.5 * data3 - 800), 0), satuBands))

        # update potential cloud pixels
        pCloudPixels = np.logical_and(pCloudPixels, hot)

        # release memory
        del hot

        # swirnir test
        # condition : Band4/Band5 > 0.75
        swirnir = np.greater((data4/data5), 0.75)

        # update potential cloud pixels
        pCloudPixels = np.logical_and(pCloudPixels, swirnir)

        # release memory
        del swirnir

        # cirrcus test
        # condition : thinProbability (Cirrus Band / 0.04)  > 0.25
        cirrcus = np.greater(thinProb, 0.25)

        # update potential cloud pixels
        pCloudPixels = np.logical_or(pCloudPixels, cirrcus)

        # release memory
        del cirrcus

        # percentile constants
        lPercentile = 0.175
        hPercentile = 1 - lPercentile

        # END OF PASS 1 #

        # PASS 2 #
        # POTENTIAL CLOUD LAYER #
        # compute cloud probability using PCPs and separate water / land clouds

        clearPixels = np.logical_and(np.logical_not(pCloudPixels), mask == 1)  # clear pixels
        ptm = 100 * clearPixels.sum() / mask.sum()  # percentage of clear pixels
        landPixels = np.logical_and(clearPixels, np.logical_not(water))  # clear lands pixels
        waterPixels = np.logical_and(clearPixels, water)  # clear water pixels
        landptm = 100 * landPixels.sum() / mask.sum()  # percentage of clear land pixels

        # check percentage of clear pixels in scene
        if ptm <= 0.001:
            # all cloud no clear pixel move to object matching
            cloud[pCloudPixels] = 1
            cloud[np.logical_not(mask)] = 0
            shadow[cloud == 0] = 1
            temp = -1

            # temperature interval for clear-sky land pixels
            tempLow = -1
            tempHigh = -1

        else:
            # if clear-land pixels cover less than 0.1 %
            # take temperature probability of all clear pixels
            if landptm >= 0.1:
                tempLand = temp[landPixels]

            else:
                tempLand = temp[clearPixels]

            # water probability #
            # temperature test

            tempWater = temp[waterPixels]  # temperature of clear water pixels

            # calculate estimated clear water temperature
            if len(tempWater) == 0:
                estWaterTemp = 0

            else:
                estWaterTemp = sp.stats.scoreatpercentile(tempWater, 100 * hPercentile)

            # clear water temperature probability
            waterTempProb = (estWaterTemp - temp) / 400
            waterTempProb[np.less(waterTempProb, 0)] = 0

            # brightness test
            # condition : min(Band5, 0.11) /  .11
            brightnessProb = np.clip((data5/1100), 0, 1)

            cloudProb = 0.125  # cloud probability 12.5 % - can be a user input

            # final water probability
            finalWaterProb = 100 * waterTempProb * brightnessProb + 100 * thinProb

            # water dynamic threshold limit
            waterThreshold = sp.stats.scoreatpercentile(finalWaterProb[waterPixels], 100 * hPercentile) + cloudProb
            # waterThreshold = 50 # old threshold limit static

            # release memory
            del waterTempProb
            del brightnessProb

            # land probability #
            # temperature test

            # calculate estimated clear land temperature interval
            if len(tempLand) != 0:
                tempLow = sp.stats.scoreatpercentile(tempLand, 100 * lPercentile)  # 0.175 percentile background temperature
                tempHigh = sp.stats.scoreatpercentile(tempLand, 100 * hPercentile)  # 0.825 percentile background temperature

            else:
                tempLow = 0
                tempHigh = 0

            # clear land temperature probability
            templ = (tempHigh + 400) - (tempLow - 400)
            landTempProb = ((tempHigh + 400) - temp) / (templ)
            landTempProb[np.less(landTempProb, 0)] = 0

            # modified NDSI and NDVI
            NDSI[np.logical_and(np.less(data2, 0), np.less(NDSI, 0))] = 0
            NDVI[np.logical_and(np.less(data3, 0), np.greater(NDSI, 0))] = 0

            # variability probability
            varProb = 1 - np.maximum(np.maximum(np.abs(NDSI), np.abs(NDVI)), whiteness)

            # release memory
            del whiteness

            # final land probability
            finalLandProb = 100 * landTempProb * varProb + 100 * thinProb

            # land dynamic threshold limit
            landThreshold = sp.stats.scoreatpercentile(finalLandProb[landPixels], 100 * hPercentile) + cloudProb

            # release memory
            del varProb
            del landTempProb
            del thinProb

            # calculate Potential Cloud Layer #
            # Condition 1   : (PCP & (finalLandProb > landThreshold) & (water == 0)) OR
            # Condition 2   : (PCP & (finalWaterProb > waterThreshold) & (water == 1)) OR
            # Condition 3   : (temp < tempLow - 3500) OR
            # Condition 4   : (finalLandProb > 99.0) & (water == 0) Small clouds don't get masked out

            condition1 = np.logical_and(np.logical_and(pCloudPixels, np.greater(finalLandProb, landThreshold)), np.logical_not(water))
            condition2 = np.logical_and(np.logical_and(pCloudPixels, np.greater(finalWaterProb, waterThreshold)), water)
            condition3 = np.less(temp, tempLow - 3500)
            condition4 = np.logical_and(np.greater(finalLandProb, 99.0), np.logical_not(water))

            # potential cloud layer
            pCloudLayer = np.logical_or(np.logical_or(condition1, condition2), condition3)

            # potential cloud mask
            cloud[pCloudLayer] = 1

            # release memory
            del finalLandProb
            del finalWaterProb
            del pCloudLayer

        # END OF PASS 2 #

        # PASS 3 #
        # POTENTIAL CLOUD SHADOW LAYER #
        # flood fill transformation for band 4 and band 5

            nir = data4.astype('float32', copy=False)
            swir = data5.astype('float32', copy=False)

            # estimate background for Band 4 & Band 5
            nirBkgrd = sp.stats.scoreatpercentile(nir[landPixels], 100.0 * lPercentile)
            swirBkgrd = sp.stats.scoreatpercentile(swir[landPixels], 100.0 * lPercentile)

            # replace bands values with background values
            nir[np.logical_not(mask)] = nirBkgrd
            swir[np.logical_not(mask)] = swirBkgrd

            # perform imfill operation for both bands
            nir = self.imfill(nir)
            swir = self.imfill(swir)
            nir = nir - data4
            swir = swir - data5

            # cloud shadow probability
            shadowProb = np.minimum(nir, swir)
            shadow[np.greater(shadowProb, 200)] = 1

            # release memory
            del nir
            del swir
            del shadowProb

        # END OF PASS 3 #

        water[np.logical_and(water == 1, cloud == 0)] = 1
        cloud = cloud.astype('uint8')
        cloud[mask == 0] = 255
        shadow[mask == 0] = 255

        return ptm, temp, tempLow, tempHigh, water, snow, cloud, shadow, dim
    # End of potentialCloudShadowSnowMask #

    # Object matching of cloud shadow layer and dilation of output mask
    def objectCloudShadowMatch(self, ptm, temp, tempLow, tempHigh, water, snow, cloud, shadow, dim):
        # final output mask to return back
        maskOutput = np.zeros(dim, 'uint8')

        sunElevationRad = math.radians(self.sunElevation)  # solar elevation angle radians
        sunAzimuthRad = math.radians(self.sunAzimuth - 90.0)  # solar azimuth angle radians

        # properties of the input scene
        cellSize = self.cellSize[0]
        height = dim[0]
        width = dim[1]

        # potential cloud & cloud shadow layer
        cloudTest = np.zeros(dim, 'uint8')
        shadowTest = np.zeros(dim, 'uint8')

        # final matched cloud & cloud shadow layer
        shadowCal = np.zeros(dim, 'uint8')
        cloudCal = np.zeros(dim, 'uint8')
        boundaryTest = np.zeros(dim, 'uint8')

        boundaryTest[cloud < 255] = 1
        shadowTest[shadow == 1] = 1
        cloudTest[cloud == 1] = 1

        # release memory
        del shadow
        del cloud

        ptmRevised = np.sum(cloudTest) / np.sum(boundaryTest)

        # full scene covered in cloud return everything as masked
        if ptm <= 0.1 or ptmRevised >= .90:
            cloudMask[cloudTest] = 1
            shadowMask[np.logical_not(cloudTest)] = 1
            similarity = -1

        else:
            # CLOUD SHADOW MATCHING #
            # constants for object matching
            tSimilar = 0.30
            tBuffer = 0.95  # threshold for matching buffering
            maxSimilar = 0.95  # max similarity threshold
            numCloudObj = 9  # minimum cloud objects
            numPixels = 3

            # enviromental lapse rate 6.5 degrees/km
            # dry adiabatic lapse rate 9.8 degrees/km

            rateELapse = 6.5
            rateDLapse = 9.8

            step = 2 * float(cellSize) * math.tan(sunElevationRad)  # move 2 pixels at a time for object matching
            if step < (2 * cellSize):
                step = 2 * cellSize  # make step = 2 for polar large solar zenith angle cases

            # get moving direction for object matching
            (rows, cols) = np.nonzero(boundaryTest)
            (yUpperLeft, num) = (rows.min(), rows.argmin())
            xUpperLeft = cols[num]

            (yLowerRight, num) = (rows.max(), rows.argmax())
            xLowerRight = cols[num]

            (xLowerLeft, num) = (cols.min(), cols.argmin())
            yLowerLeft = rows[num]

            (xUpperRight, num) = (cols.max(), cols.argmax())
            yUpperRight = rows[num]

            # calculate view angle geometry
            (A, B, C, omigaPar, omigaPer) = self.viewgeo(float(xUpperLeft), float(yUpperLeft), float(xUpperRight), float(yUpperRight),
                                                         float(xLowerLeft), float(yLowerLeft), float(xLowerRight), float(yLowerRight))

            # segmentation of each cloud object
            (segmCloud, segmCloudFeatures) = sp.ndimage.measurements.label(cloudTest, sp.ndimage.morphology.generate_binary_structure(2, 2))

            # filter out each cloud object with < than 9 pixels (numCloudObj)
            morphology.remove_small_objects(segmCloud, numCloudObj, in_place=True)
            segmCloud, fm, invm = segmentation.relabel_sequential(segmCloud)

            num = np.max(segmCloud)  # Number of cloud objects
            cloudProp = measure.regionprops(segmCloud)  # properties of each cloud object
            similarity = np.zeros(num)  # cloud shadow match similarity

            for cloudObj in cloudProp:

                cloudArea = cloudObj['Area']
                cloudLabel = cloudObj['Label']
                numCloudPixels = cloudArea

                xyType = np.zeros((2, numCloudPixels), dtype='uint32')  # moving cloud xy
                tempxyType = np.zeros((2, numCloudPixels), dtype='uint32')  # record the max threshold moving cloud xy
                tempxys = np.zeros((2, numCloudPixels))  # corrected for view angle xy

                cloudCoord = (cloudObj['Coordinates'][:,0], cloudObj['Coordinates'][:, 1])  # cloud pixellist coordinates (x,y)
                tempObj = temp[cloudCoord]  # temperature of the cloud object
                rObj = math.sqrt(cloudArea / 2 * math.pi)  # used for getting influenced cloud BT

                tempCloudBase = math.pow(rObj - 8, 2) / math.pow(rObj, 2)
                tempCloudBase = np.minimum(tempCloudBase, 1)  # temp of edge pixel should be less than 1
                baseThreshold = sp.stats.mstats.mquantiles(tempObj, tempCloudBase)

                tempObj[tempObj > baseThreshold] = baseThreshold  # replace edge of cloud with baseThreshold

                maxCloudHeight = 12000  # maximum cloud base height (m)
                minCloudHeight = 200  # minimum cloud base height (m)

                # refined cloud height range (m) dynamic
                # minCloudHeight = max(minCloudHeight, int(10 *(tempLow - 400 - baseThreshold) / rateDLapse)) # Removed from Matlab code
                # maxCloudHeight = min(maxCloudHeight, int(10 *(tempHigh + 400 - baseThreshold)))  # Removed from Matlab code

                # height and similarity variable
                recordHeight = 0.0
                recordThreshold = 0.0

                # iterate cloud base height from predicted min to max
                # check if cloud base height less than predicted max
                for baseHeight in np.arange(minCloudHeight, maxCloudHeight, step):

                    # get the true postion of the cloud
                    # calculate cloud DEM with initial base height
                    h = baseHeight
                    # height = (10 * (baseThreshold - tempObj) / rateELapse + baseHeight)  # removed from Matlab code

                    # Return turn (x, y) coordinates of cloud
                    tempxys[1, :], tempxys[0, :] = self.matTrueCloud(cloudCoord[1], cloudCoord[0], h, A, B, C, omigaPar, omigaPer)

                    xyMove = h / (cellSize * math.tan(sunElevationRad))

                    if self.sunAzimuth < 180:
                        xyType[1, :] = np.round(tempxys[1, :] - xyMove * math.cos(sunAzimuthRad))  # X is for j, 1
                        xyType[0, :] = np.round(tempxys[0, :] - xyMove * math.sin(sunAzimuthRad))  # Y is for i, 0

                    else:
                        xyType[1, :] = np.round(tempxys[1, :] + xyMove * math.cos(sunAzimuthRad))  # X is for j, 1
                        xyType[0, :] = np.round(tempxys[0, :] + xyMove * math.sin(sunAzimuthRad))  # Y is for i, 0

                    tempCol = xyType[1, :]  # column
                    tempRow = xyType[0, :]  # row

                    outId = (tempRow < 0) | (tempRow >= height) | (tempCol < 0) | (tempCol >= width)  # id out of input scene
                    outAll = np.sum(outId)

                    tempFCol = tempCol[outId == 0]
                    tempFRow = tempRow[outId == 0]

                    tempId = [tempFRow, tempFCol]

                    # matched id - exclude original cloud
                    matchId = (boundaryTest[tempId] == 0) | ((segmCloud[tempId] != cloudLabel) & ((cloudTest[tempId] > 0) | (shadowTest[tempId] == 1)))
                    matchedAll = np.sum(matchId) + outAll

                    # total pixel id - exclude original cloud
                    totalId = segmCloud[tempId] != cloudLabel
                    totalAll = np.sum(totalId) + outAll

                    # Similarity Threshold Calculation #
                    thresholdMatch = np.float32(matchedAll) / totalAll

                    if (thresholdMatch >= (tBuffer * recordThreshold)) and (baseHeight < (maxCloudHeight - step)) and (recordThreshold < maxSimilar):
                        if thresholdMatch > recordThreshold:
                            recordThreshold = thresholdMatch
                            recordHeight = h

                    elif recordThreshold > tSimilar:
                        similarity[cloudLabel - 1] = recordThreshold
                        moveThreshold = recordHeight / (cellSize * math.tan(sunElevationRad))

                        if self.sunAzimuth < 180:
                            tempxyType[1, :] = np.round(tempxys[1, :] - moveThreshold * math.cos(sunAzimuthRad))  # X is for col j,2
                            tempxyType[0, :] = np.round(tempxys[0, :] - moveThreshold * math.sin(sunAzimuthRad))  # Y is for row i,1

                        else:

                            tempxyType[1, :] = np.round(tempxys[1, :] + moveThreshold * math.cos(sunAzimuthRad))  # X is for col j,2
                            tempxyType[0, :] = np.round(tempxys[0, :] + moveThreshold * math.sin(sunAzimuthRad))  # Y is for row i,1

                        tempSCol = tempxyType[1, :]
                        tempSRow = tempxyType[0, :]

                        # put data within range
                        tempSRow[tempSRow < 0] = 0
                        tempSRow[tempSRow >= height] = height - 1
                        tempSCol[tempSCol < 0] = 0
                        tempSCol[tempSCol >= width] = width - 1

                        tempSId = [tempSRow, tempSCol]
                        shadowCal[tempSId] = 1

                        break

                    else:
                        recordThreshold = 0.0
                        # End of Similarity Threshold Calculation #

            # dilate final output masks
            dilateKernel = np.ones((3, 3), 'uint8')

            shadowCal = sp.ndimage.morphology.binary_dilation(shadowCal, structure=dilateKernel)  # dilate shadow layer
            segmCloudTemp = (segmCloud != 0)
            cloudCal = sp.ndimage.morphology.binary_dilation(segmCloudTemp, structure=dilateKernel)  # dilate Cloud layer
            snow = sp.ndimage.morphology.binary_dilation(snow, structure=dilateKernel)  # dilate Snow layer

        maskOutput[boundaryTest == 0] = 255

        if self.mode == "Mask Snow":
            maskOutput[snow == 1] = 1

        elif self.mode == "Mask Cloud & Cloud Shadow":
            maskOutput[shadowCal == 1] = 1
            maskOutput[cloudCal == 1] = 1

        elif self.mode == "Mask Cloud":
            maskOutput[cloudCal == 1] = 1

        else:
            maskOutput[cloudCal == 1] = 1
            maskOutput[shadowCal == 1] = 1
            maskOutput[snow == 1] = 1

        return maskOutput

    # matTrueCloud - calculate shadow pixel locations of a true cloud segment
    def matTrueCloud(self, x, y, h, A, B, C, omigaPar, omigaPer):

        avgHeight = 705000  # average Landsat height (m)
        dist = (A * x + B * y + C) / math.sqrt(A * A + B * B)
        distPar = dist / math.cos(omigaPer - omigaPar)
        distMove = distPar * h / avgHeight  # cloud move distance (m)
        deltX = distMove * math.cos(omigaPar)
        deltY = distMove * math.sin(omigaPar)

        xNew = x + deltX  # new x, j
        yNew = y + deltY  # new y, i

        return (xNew, yNew)

    # viewgeo - Calculate the geometric parameters needed for the cloud/shadow match
    def viewgeo(self, xUpperLeft, yUpperLeft, xUpperRight, yUpperRight, xLowerLeft, yLowerLeft, xLowerRight, yLowerRight):

        xUpper = (xUpperLeft + xUpperRight) / 2
        xLower = (xLowerLeft + xLowerRight) / 2
        yUpper = (yUpperLeft + yUpperRight) / 2
        yLower = (yLowerLeft + yLowerRight) / 2

        # get k of the upper left and right points
        if (xUpperLeft != xUpperRight):
            kUpper = (yUpperLeft - yUpperRight) / (xUpperLeft - xUpperRight)

        else:
            kUpper = 0.0

        # get k of the lower left and right points
        if (xLowerLeft != xLowerRight):
            kLower = (yLowerLeft - yLowerRight) / (xLowerLeft - xLowerRight)

        else:
            kLower = 0.0

        kAverage = (kUpper + kLower) / 2
        omigaPar = math.atan(kAverage)  # get the angle of parallel lines

        A = yUpper - yLower
        B = xLower - xUpper
        C = yLower * xUpper - xLower * yUpper

        omigaPer = math.atan(B / A)  # get the angle which is perpendicular to the trace line

        return (A, B, C, omigaPar, omigaPer)

    # calculate NDVI
    def calculateNDVI(self, pixels, bandId):
        NDVI = (pixels[bandId[3]] - pixels[bandId[2]])/(pixels[bandId[3]] + pixels[bandId[2]])
        NDVI[(pixels[bandId[3]] + pixels[bandId[2]]) == 0] = 0.01

        return NDVI

    # calculate NDSI
    def calculateNDSI(self, pixels, bandId):
        NDSI = (pixels[bandId[1]] - pixels[bandId[4]])/(pixels[bandId[1]] + pixels[bandId[4]])
        NDSI[(pixels[bandId[1]] + pixels[bandId[4]]) == 0] = 0.01

        return NDSI

    # imfill - flood-fill transformation : fills image regions and holes
    def imfill(self, band):
        seed = band.copy()
        seed[1:-1, 1:-1] = band.max()   # borders masked with maximum value of image
        filled = morphology.reconstruction(seed, band, method='erosion')  # fill the holes - Equivalent to imfill

        return filled

"""
References:
    [1]. Zhu, Z. and Woodcock, C. E.,
    Object-based cloud and cloud shadow detection in Landsat imagery, Remote Sensing of Environment (2012)
    [2]. Zhu, Z. and Woodcock, C. E.,
    Improvement and Expansion of the Fmask Algorithm: Cloud, Cloud Shadow, and Snow Detection for Landsats 4-7, 8, and Sentinel 2 Images, Remote Sensing of Environment
    [3]. FMask: Automated clouds, cloud shadows, and snow masking for Landsat 4, 5, 7, and 8 images.
    https://code.google.com/p/fmask/
    [4]. CFMask: C version of the Fmask cloud algorithm by Zhe Zhu at Boston University
    https://code.google.com/p/cfmask/
"""
