import math
import numpy as np
import scipy as sp
from skimage import morphology, measure, segmentation


class FMask():

    def __init__(self):
        self.name = "FMask Function"
        self.description = "Performs masking of Clouds, Clouds Shadow & Snow in Landsat imagery"
        self.sunElevation = None  # sun elevation angle
        self.sunAzimuth = None  # sun azimuth angle
        self.sensorName = None  # satellite sensor name

    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Reflectance Raster",
                'description': ("Top of Atmosphere Reflectance Raster. "
                                "(Landsat 5 and 7: bands 1, 2, 3, 4, 5 and 7; "
                                "Landsat 8: bands 1, 2, 3, 4, 5, 6, 7 and 9)")
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Thermal Raster",
                'description': ("Thermal Raster. "
                                "(Landsat 5 and 7: band 6; "
                                "Landsat 8: band 10)")
            },
            {
                'name': 'mask',
                'dataType': 'string',
                'value': 'Mask Cloud',
                'required': True,
                'domain': ('Mask Cloud', 'Mask Water', 'Mask Snow',
                           'Mask Cloud Shadow', 'Mask Cloud, Snow & Water'),
                'displayName': "Masking Feature",
                'description': "Select masking feature to apply on Landsat imagery."
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,                               # inherit everything but the pixel type (1)
          'invalidateProperties': 2 | 4 | 8,                            # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                                                 # no padding on each of the input pixel block
          'inputMask': True,                                            # we need the input mask in .updatePixels()
          'keyMetadata': ('sensorname', 'sunazimuth', 'sunelevation'),  # key property used in cloud shadow detection
        }

    def updateRasterInfo(self, **kwargs):
        # get masking feature
        self.mask = kwargs['mask']

        # get key metadata from input raster
        # used for cloud shadow detection
        self.sunElevation = kwargs['r1_keyMetadata'].get("sunelevation")
        self.sunAzimuth = kwargs['r1_keyMetadata'].get("sunazimuth")
        self.sensorName = kwargs['r1_keyMetadata'].get('sensorname').replace("-"," ")

        # check key metadata values
        if (self.sunAzimuth is None or self.sunElevation is None or self.sensorName is None or
           not(isinstance(self.sunAzimuth, float)) or not(isinstance(self.sunElevation, float)) or not(isinstance(self.sensorName, str))):
            raise Exception("Error: Key Metadata values not valid.")

        if self.sensorName[0:9] != "Landsat 8" and self.sensorName[0:9] != "Landsat 7" and self.sensorName[0:9] != "Landsat 5" :
            raise Exception("Error: FMask function only works on Landsat 8, 7 and 5 imagery.")

        # get resolution of the input raster
        # used for calculating steps of iterations in cloud shadow detection
        self.cellSize = kwargs['r1_info']['cellSize']

        # output raster information
        kwargs['output_info']['bandCount'] = kwargs['r1_info']['bandCount']
        kwargs['output_info']['resampling'] = False
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get input TOA reflectance multispectral bands
        pixels = np.array(pixelBlocks['r1_pixels'], dtype='f4', copy=False)

        # get input thermal band of landsat scene
        # convert thermal band values to brightness temperature
        temperature = self.getScaledTemperature(np.array(pixelBlocks['r2_pixels'], dtype='f4', copy=False))

        # calculate potential cloud, cloud shadow, snow masks - getPotentialMasks
        # cloud object matching for cloud shadow detection - matchCloudObjects
        ptm, temperature, tempLow, tempHigh, water, snow, cloud, shadow = self.getPotentialMasks(pixels, temperature)
        fmask = self.matchCloudObjects(ptm, temperature, tempLow, tempHigh, water, snow, cloud, shadow)

        # output pixel arrays of multispectral bands with masked features
        pixelBlocks['output_pixels'] = pixels.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = np.array([np.logical_not(fmask)] * shape[0]).astype('u1', copy=False)

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

    def getScaledTemperature(self, temperature):
        # check if thermal band from raster product or single thermal band added
        temperature = temperature[0] if len(temperature.shape) > 2 else temperature

        # assign thermal band properties depending on sensor name
        if self.sensorName == "Landsat 8":
            k1 = 774.89  # thermal conversion constant K1
            k2 = 1321.08  # thermal conversion constant K2
            lmax = 22.00180  # thermal band MAX_RADIANCE
            lmin = 0.10033  # thermal band MIN_RADIANCE
            dn = 65534  # digital number limit
        elif self.sensorName == "Landsat 7":
            k1 = 666.09
            k2 = 1282.71
            lmax = 17.04
            lmin = 0.0
            dn = 244
        else:
            k1 = 607.76
            k2 = 1260.56
            lmax = 15.303
            lmin = 1.238
            dn = 244

        # convert thermal band value to brightness temperature
        temperature = ((lmax - lmin)/dn) * temperature + lmin

        # calculate deg. celsius difference
        temperature = 100 * ((k2 / np.log((k1 / temperature) + 1)) - 273.15)

        return temperature

    # assign bandIDs for reference in multispectral bands
    def getBandIDs(self):
        if self.sensorName == "Landsat 8": return [1, 2, 3, 4, 5, 6, 7]
        else: return [0, 1, 2, 3, 4, 5]

    # Identify the potential cloud pixels, snow pixels, water pixels,
    # clear land pixels, and shadow pixels
    def getPotentialMasks(self, pixels, temperature):
        dim = pixels[0].shape  # dimensions of imagery

        bandIDs = self.getBandIDs()  # get bandIDs depending on landsat scene

        # cirrus band probability for Landsat 8 imagery
        if self.sensorName == "Landsat 8": thinProb = (10**4) * pixels[-1] / 400
        else:                              thinProb = 0

        cloud = np.zeros(dim, 'uint8')  # cloud mask
        snow = np.zeros(dim, 'uint8')  # snow mask
        water = np.zeros(dim, 'uint8')  # water mask
        shadow = np.zeros(dim, 'uint8')  # shadow mask

        # assignment of Landsat bands to temporary variables
        mulFactor = (10**4)
        band1 = mulFactor * pixels[bandIDs[0]]
        band2 = mulFactor * pixels[bandIDs[1]]
        band3 = mulFactor * pixels[bandIDs[2]]
        band4 = mulFactor * pixels[bandIDs[3]]
        band5 = mulFactor * pixels[bandIDs[4]]
        band6 = mulFactor * pixels[bandIDs[5]]

        NDSI = (band2 - band5)/(band2 + band5)  # normalized difference snow index (NDSI)
        NDSI[np.equal((band2 + band5), 0)] = 0.01

        NDVI = (band4 - band3)/(band4 + band3)  # normalized difference vegetation index (NDVI)
        NDVI[np.equal((band4 + band3), 0)] = 0.01

        # release memory
        del pixels
        del bandIDs

        mask = np.greater(temperature, -9999)  # overlapping region of thermal band and multispectral bands

        # saturation test for visible bands 1, 2 and 3
        saturatedBands = np.logical_or(np.less(band1, 0), np.logical_or(np.less(band2, 0), np.less(band3, 0)))

        # PASS 1 #
        # POTENTIAL CLOUD PIXELS #
        # perform multiple spectral tests to obtain potential cloud pixels

        # basic test
        # condition : band 7 > 0:03 and Brightness Temperature < 27 and NDSI < 0.8 and NDVI < 0.8
        pCloudPixels = np.logical_and(np.logical_and(np.less(NDSI, 0.8), np.less(NDVI, 0.8)),
                                      np.logical_and(np.greater(band6, 300), np.less(temperature, 2700)))

        # snow test
        # condition: NDSI > 0.15 and Brightness Temperature < 3.8 and band 4 > 0.11 and band 2 > 0.1
        # OR condition used to include all pixels between thin / thick clouds
        snowCondition = np.logical_or(np.logical_and(np.greater(NDSI, 0.15), np.logical_and(np.greater(band4, 1100),
                                      np.greater(band2, 1000))), np.less(temperature, 400))

        # mask snow in array
        snow[snowCondition] = 1
        snow[mask == 0] = 255

        # water test
        # condition : (NDVI < 0.01 and band 4 < 0.11) or (NDVI < 0.1 and NDVI > 0 and band 4 < 0.05)
        waterCondition = np.logical_or(np.logical_and(np.less(NDVI, 0.01), np.less(band4, 1100)),
                                       np.logical_and(np.logical_and(np.less(NDVI, 0.1), np.greater(NDVI, 0)),
                                       np.less(band4, 500)))

        # mask water in array
        water[waterCondition] = 1
        water[mask == 0] = 255

        # whiteness test
        # condition : (Sum(band (1, 2, 3) - mean)/ mean) < 0.7
        # mean of visible bands 1, 2, 3
        intensity = (band1 + band2 + band3)/3
        whiteness = (np.abs(band1 - intensity) + np.abs(band2 - intensity) + np.abs(band3 - intensity)) / intensity
        whiteness[saturatedBands] = 0

        del intensity  # release memory

        # update potential cloud pixels
        pCloudPixels = np.logical_and(pCloudPixels, np.less(whiteness, 0.7))

        # hot (haze optimized transformation) test
        # condition : band 1 - 0.5 * band 3 - 0.08 > 0
        hot = (np.logical_or(np.greater((band1 - 0.5 * band3 - 800), 0), saturatedBands))

        pCloudPixels = np.logical_and(pCloudPixels, hot)  # update potential cloud pixels

        del hot  # release memory

        # swirnir test
        # condition : band 4 / band 5 > 0.75
        swirnir = np.greater((band4 / band5), 0.75)

        # update potential cloud pixels
        pCloudPixels = np.logical_and(pCloudPixels, swirnir)

        del swirnir  # release memory

        # cirrcus test
        # condition : thinProbability (Cirrus Band / 0.04)  > 0.25
        cirrcus = np.greater(thinProb, 0.25)

        pCloudPixels = np.logical_or(pCloudPixels, cirrcus)  # update potential cloud pixels

        del cirrcus  # release memory

        # END OF PASS 1 #
        # POTENTIAL CLOUD LAYER #
        # compute cloud probability using PCPs and separate water / land clouds

        # percentile constants
        lPercentile = 0.175
        hPercentile = 1 - lPercentile

        clearPixels = np.logical_and(np.logical_not(pCloudPixels), mask == 1)  # clear pixels
        ptm = 100. * clearPixels.sum() / mask.sum()  # percentage of clear pixels
        landPixels = np.logical_and(clearPixels, np.logical_not(water))  # clear lands pixels
        waterPixels = np.logical_and(clearPixels, water)  # clear water pixels
        landptm = 100. * landPixels.sum() / mask.sum()  # percentage of clear land pixels

        # check percentage of clear pixels in scene
        if ptm <= 0.001:
            # all cloud no clear pixel move to object matching
            cloud[:] = 1
            cloud[np.logical_not(mask)] = 0
            shadow[cloud == 0] = 1
            temperature = -1

            # temperature interval for clear-sky land pixels
            tempLow = -1
            tempHigh = -1
        else:
            # if clear-land pixels cover less than 0.1 %
            # take temperature probability of all clear pixels
            if landptm >= 0.1:  tempLand = temperature[landPixels]
            else:               tempLand = temperature[clearPixels]

            # water probability #
            # temperature test
            # temperature of clear water pixels
            tempWater = temperature[waterPixels]

            # calculate estimated clear water temperature
            if len(tempWater) == 0:  estWaterTemp = 0
            else:                    estWaterTemp = sp.stats.scoreatpercentile(tempWater, 100 * hPercentile)

            # clear water temperature probability
            waterTempProb = (estWaterTemp - temperature) / 400
            waterTempProb[np.less(waterTempProb, 0)] = 0

            # brightness test # condition : min(Band5, 0.11) /  .11
            brightnessProb = np.clip((band5 / 1100), 0, 1)

            cloudProb = 0.125  # cloud probability 12.5 %
            finalWaterProb = 100 * waterTempProb * brightnessProb + 100 * thinProb
            waterThreshold = sp.stats.scoreatpercentile(finalWaterProb[waterPixels], 100 * hPercentile) + cloudProb

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
            landTempProb = ((tempHigh + 400) - temperature) / (templ)
            landTempProb[np.less(landTempProb, 0)] = 0

            # modified NDSI and NDVI
            NDSI[np.logical_and(np.less(band2, 0), np.less(NDSI, 0))] = 0
            NDVI[np.logical_and(np.less(band3, 0), np.greater(NDSI, 0))] = 0

            varProb = 1 - np.maximum(np.maximum(np.abs(NDSI), np.abs(NDVI)), whiteness)  # variability probability

            del whiteness  # release memory

            finalLandProb = 100 * landTempProb * varProb + 100 * thinProb
            landThreshold = sp.stats.scoreatpercentile(finalLandProb[landPixels], 100 * hPercentile) + cloudProb

            # release memory
            del varProb
            del landTempProb
            del thinProb

            # calculate Potential Cloud Layer #
            # C1 : (PCP & (finalLandProb > landThreshold) & (water == 0)) OR
            # C2 : (PCP & (finalWaterProb > waterThreshold) & (water == 1)) OR
            # C3 : (temperature < tempLow - 3500) OR
            # C4 : (finalLandProb > 99.0) & (water == 0) small clouds don't get masked out

            c1 = np.logical_and(np.logical_and(pCloudPixels, np.greater(finalLandProb, landThreshold)), np.logical_not(water))
            c2 = np.logical_and(np.logical_and(pCloudPixels, np.greater(finalWaterProb, waterThreshold)), water)
            c3 = np.less(temperature, tempLow - 3500)
            c4 = np.logical_and(np.greater(finalLandProb, 99.0), np.logical_not(water))

            pCloudLayer = np.logical_or(np.logical_or(c1, c2), c3)  # potential cloud layer

            cloud[pCloudLayer] = 1  # potential cloud mask

            # release memory
            del finalLandProb
            del finalWaterProb
            del pCloudLayer

        # END OF PASS 2 #

        # PASS 3 #
        # POTENTIAL CLOUD SHADOW LAYER #
        # flood fill transformation for band 4 and band 5

            nir = band4.astype('float32', copy=False)
            swir = band5.astype('float32', copy=False)

            # estimate background for Band 4 & Band 5
            nirBkgrd = sp.stats.scoreatpercentile(nir[landPixels], 100.0 * lPercentile)
            swirBkgrd = sp.stats.scoreatpercentile(swir[landPixels], 100.0 * lPercentile)

            # replace bands values with background values
            nir[np.logical_not(mask)] = nirBkgrd
            swir[np.logical_not(mask)] = swirBkgrd

            # perform imfill operation for both bands
            nir = self.imfill(nir)
            swir = self.imfill(swir)
            nir = nir - band4
            swir = swir - band5

            # cloud shadow probability
            shadowProb = np.minimum(nir, swir)
            shadow[np.greater(shadowProb, 200)] = 1

            # release memory
            del nir
            del swir
            del shadowProb

        # END OF PASS 3 #

        cloud = cloud.astype('uint8')
        cloud[mask == 0] = 255
        shadow[mask == 0] = 255
        water[np.logical_and(water == 1, cloud == 0)] = 1

        return ptm, temperature, tempLow, tempHigh, water, snow, cloud, shadow

    # Object matching of cloud shadow layer and dilation of output mask
    def matchCloudObjects(self, ptm, temperature, tempLow, tempHigh, water, snow, cloud, shadow):
        dim = cloud.shape  # dimensions of single band
        fmask = np.zeros(dim, 'uint8')  # final output mask to return back
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
        snowCal = np.zeros(dim, 'uint8')

        boundaryTest[cloud < 255] = 1
        shadowTest[shadow == 1] = 1
        cloudTest[cloud == 1] = 1

        ptmRevised = float(np.sum(cloudTest)) / np.sum(boundaryTest)  # revised percentage of cloud pixels

        # full scene covered in cloud return everything as masked
        if ptm <= 0.001 or ptmRevised >= .90:
            cloudCal[:] = 1
            shadowCal[:] = 1
            water[:] = 1
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
            if step < (2 * cellSize):   step = 2 * cellSize  # make step = 2 for polar large solar zenith angle cases

            # get moving direction for object matching
            (xUpperLeft, yUpperLeft, yLowerRight, xLowerRight, xLowerLeft, yLowerLeft, xUpperRight, yUpperRight) = self.getMovingDirection(boundaryTest)

            # calculate view angle geometry
            (A, B, C, omegaPara, omegaPerp) = self.viewgeo(float(xUpperLeft), float(yUpperLeft), float(xUpperRight), float(yUpperRight),
                                                           float(xLowerLeft), float(yLowerLeft), float(xLowerRight), float(yLowerRight))

            # segmentation of each cloud object
            (segmCloud, segmCloudFeatures) = sp.ndimage.measurements.label(cloudTest, sp.ndimage.morphology.generate_binary_structure(2, 2))

            # filter out each cloud object with < than 9 pixels (numCloudObj)
            morphology.remove_small_objects(segmCloud, numCloudObj, in_place=True)
            segmCloud, fm, invm = segmentation.relabel_sequential(segmCloud)

            num = np.max(segmCloud)  # number of cloud objects
            cloudProp = measure.regionprops(segmCloud)  # properties of each cloud object
            similarity = np.zeros(num)  # cloud shadow match similarity

            for cloudObj in cloudProp:

                cloudArea = cloudObj['Area']
                cloudLabel = cloudObj['Label']
                numCloudPixels = cloudArea

                xyType = np.zeros((2, numCloudPixels), dtype='uint32')  # moving cloud xy
                tempxyType = np.zeros((2, numCloudPixels), dtype='uint32')  # record the max threshold moving cloud xy
                tempxys = np.zeros((2, numCloudPixels))  # corrected for view angle xy

                cloudCoord = (cloudObj['Coordinates'][:, 0], cloudObj['Coordinates'][:, 1])  # cloud pixellist coordinates (x,y)
                tempObj = temperature[cloudCoord]  # temperature of the cloud object
                rObj = math.sqrt(cloudArea / 2 * math.pi)  # used for getting influenced cloud BT

                tempCloudBase = math.pow(rObj - 8, 2) / math.pow(rObj, 2)
                tempCloudBase = np.minimum(tempCloudBase, 1)  # temp of edge pixel should be less than 1
                baseThreshold = sp.stats.mstats.mquantiles(tempObj, tempCloudBase)

                tempObj[tempObj > baseThreshold] = baseThreshold  # replace edge of cloud with baseThreshold

                maxCloudHeight = 12000  # maximum cloud base height (m)
                minCloudHeight = 200  # minimum cloud base height (m)

                # height and similarity variable
                recordHeight = 0.0
                recordThreshold = 0.0

                # iterate cloud base height from predicted min to max
                # check if cloud base height less than predicted max
                for baseHeight in np.arange(minCloudHeight, maxCloudHeight, step):
                    # get the true postion of the cloud
                    # calculate cloud DEM with initial base height
                    h = baseHeight

                    # Return turn (x, y) coordinates of cloud
                    tempxys[1, :], tempxys[0, :] = self.calcTrueCloudSegment(cloudCoord[1], cloudCoord[0], h, A, B, C, omegaPara, omegaPerp)

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

                        shadowCal[tempSId] = 1  # mask shadow in array
                        break
                    else:
                        recordThreshold = 0.0

                    # End of Similarity Threshold Calculation #

            # dilate final output masks
            dilateKernel = np.ones((3, 3), 'uint8')

            shadowCal = sp.ndimage.morphology.binary_dilation(shadowCal, structure=dilateKernel)  # dilate shadow layer
            cloudCal = sp.ndimage.morphology.binary_dilation((segmCloud != 0), structure=dilateKernel)  # dilate cloud layer
            snow = sp.ndimage.morphology.binary_dilation(snow, structure=dilateKernel)  # dilate snow layer

        fmask[boundaryTest == 0] = 255

        if self.mask == "Mask Snow":                    fmask[snow == 1] = 1
        elif self.mask == "Mask Cloud":                 fmask[cloudCal == 1] = 1
        elif self.mask == "Mask Water":                 fmask[water == 1] = 1
        elif self.mask == "Mask Cloud Shadow":          fmask[np.logical_or(shadowCal == 1, cloudCal == 1)] = 1
        else:                                           fmask[np.logical_or(np.logical_or(cloudCal == 1, water == 1), snow == 1)] = 1

        return fmask

    # getMovingDirection - moving direction for cloud object matching
    def getMovingDirection(self, boundaryTest):

        (rows, cols) = np.nonzero(boundaryTest)
        (yUpperLeft, num) = (rows.min(), rows.argmin())
        xUpperLeft = cols[num]

        (yLowerRight, num) = (rows.max(), rows.argmax())
        xLowerRight = cols[num]

        (xLowerLeft, num) = (cols.min(), cols.argmin())
        yLowerLeft = rows[num]

        (xUpperRight, num) = (cols.max(), cols.argmax())
        yUpperRight = rows[num]

        return (xUpperLeft, yUpperLeft, yLowerRight, xLowerRight, xLowerLeft, yLowerLeft, xUpperRight, yUpperRight)

    # calcTrueCloudSegment - calculate shadow pixel locations of a true cloud segment
    def calcTrueCloudSegment(self, x, y, h, A, B, C, omegaPara, omegaPerp):

        avgHeight = 705000  # average Landsat height (m)
        dist = (A * x + B * y + C) / math.sqrt(A * A + B * B)
        distPara = dist / math.cos(omegaPerp - omegaPara)
        distMove = distPara * h / avgHeight  # cloud move distance (m)
        deltaX = distMove * math.cos(omegaPara)
        deltaY = distMove * math.sin(omegaPara)

        xNew = x + deltaX  # new x, j
        yNew = y + deltaY  # new y, i

        return (xNew, yNew)

    # viewgeo - calculate the geometric parameters needed for the cloud/shadow match
    def viewgeo(self, xUpperLeft, yUpperLeft, xUpperRight, yUpperRight, xLowerLeft, yLowerLeft, xLowerRight, yLowerRight):

        xUpper = (xUpperLeft + xUpperRight) / 2
        xLower = (xLowerLeft + xLowerRight) / 2
        yUpper = (yUpperLeft + yUpperRight) / 2
        yLower = (yLowerLeft + yLowerRight) / 2

        # get k of the upper left and right points
        if (xUpperLeft != xUpperRight):  kUpper = (yUpperLeft - yUpperRight) / (xUpperLeft - xUpperRight)
        else:                            kUpper = 0.0

        # get k of the lower left and right points
        if (xLowerLeft != xLowerRight):  kLower = (yLowerLeft - yLowerRight) / (xLowerLeft - xLowerRight)
        else:                            kLower = 0.0

        kAverage = (kUpper + kLower) / 2
        omegaPara = math.atan(kAverage)  # get the angle of parallel lines

        A = yUpper - yLower
        B = xLower - xUpper
        C = yLower * xUpper - xLower * yUpper

        omegaPerp = math.atan(B / A)  # get the angle which is perpendicular to the trace line

        return (A, B, C, omegaPara, omegaPerp)

    # imfill - flood-fill transformation : fills image regions and holes
    def imfill(self, band):
        seed = band.copy()
        seed[1:-1, 1:-1] = band.max()  # borders masked with maximum value of image
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
