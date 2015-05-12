import numpy as np
import math
import scipy.stats, scipy.signal, scipy.ndimage.morphology
from skimage import morphology, measure, segmentation

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
                'description': ("Landsat Imagery. Nth Band = Thermal Band")
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
                'value': 'Only Cloud',
                'required': True,
                'domain': ('Only Cloud' , 'Cloud + Shadow',  'Only Snow', "All"),
                'displayName': "Masking Feature",
                'description': "Mask feature from Landsat Scene"
            },
            {
                'name': 'albedo',
                'dataType': 'string',
                'value': 'True',
                'required': True,
                'domain': ('True','False'),
                'displayName': "Albedo Values",
                'description': "Input TOAs in Albedo or not?"
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,            # inherit everything but the pixel type (1) and no Data (2)
          'invalidateProperties': 2 | 4 | 8,     # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 0,                          # no padding on each of the input pixel block
          'inputMask': False,                    # we don't need the input mask in .updatePixels()
          'keyMetadata': ('sunazimuth', 'sunelevation'),  # we can use this key property in Object Matching of Cloud and Cloud Shadow
        }

    def updateRasterInfo(self, **kwargs):
        ## Input Parameters ##

        self.prepare(scene = kwargs.get("type","Landsat 8"),
                     mode = kwargs.get("mode", "Only Cloud"),albedo = kwargs.get("albedo", "True"),
                     sunElevation = kwargs['raster_keyMetadata'].get("sunelevation"),
                     sunAzimuth = kwargs['raster_keyMetadata'].get("sunazimuth"), resolu = kwargs['raster_info']['cellSize'])

        if self.scene == "Landsat 8":
            kwargs['output_info']['bandCount'] = 9
        else:
            kwargs['output_info']['bandCount'] = 7

        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['noData'] = np.array([255,])
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        landsat     = np.array(pixelBlocks['raster_pixels'], dtype ='f4', copy=False)
        fmask       = np.zeros(landsat.shape)

        ## calculate dependent variables ##
        landsat      = self.convertScene(landsat)
        self.NDSI    = self.calculateNDSI(landsat)
        self.NDVI    = self.calculateNDVI(landsat)

        ## perform masking operation ##
        fmaskOutput  = self.potential_cloud_shadow_snow_mask(landsat)

        for band in xrange(landsat.shape[0]):
            fmask[band]     = np.where(fmaskOutput , 255 , landsat[band])

        pixelBlocks['output_pixels'] = fmask.astype('f4', copy=False)   # Change to i1 (0 to 255) pixelType

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

    def prepare(self, scene = "Landsat 8", mode = "Only Cloud", albedo = "True" , sunElevation = None , sunAzimuth = None, resolu = (30,30)):

        # Assignment of Public Variables
        self.scene, self.mode, self.albedo = scene, mode, albedo
        self.sunEle, self.sunAzi, self.resolu = sunElevation, sunAzimuth,resolu

        if scene == "Landsat 8":
            self.K1 , self.K2       = 774.89 , 1321.08          # Thermal Conversion Constants
            self.Lmax , self.Lmin   = 22.00180 ,  0.10033       # Radiance Thermal Bands Min_Max
            self.DN                 = 65534                     # Digital Number Limit
            self.bandID             = [1, 2, 3, 4, 5, 6, 7, 8]  # Band IDs

        elif scene == "Landsat 7":
            self.K1, self.K2        = 666.09 , 1282.71
            self.Lmax , self.Lmin   = 17.04 , 0.0
            self.DN                 = 244
            self.bandID             = [0, 1, 2, 3, 4, 5, 6]

        else:
            self.K1, self.K2        = 607.76 , 1260.56
            self.Lmax , self.Lmin   = 15.303 , 1.238
            self.DN                 = 244
            self.bandID             = [0, 1, 2, 3, 4, 5, 6]


    # Calculate Brightness Temperature from Thermal Band
    def convertScene(self, landsat):
        landsat[-1] = ((self.Lmax - self.Lmin) / self.DN) * landsat[-1] + self.Lmin
        landsat[-1] = 100 * (((self.K2/np.log((self.K1/landsat[-1])+1))) - 273.15)   # Convert to Celsius

        return landsat

    # Calculate NDVI
    def calculateNDVI(self, landsat):
        NDVI     = (landsat[self.bandID[3]] - landsat[self.bandID[2]])/(landsat[self.bandID[3]] + landsat[self.bandID[2]])
        NDVI[(landsat[self.bandID[3]] + landsat[self.bandID[2]])== 0] = 0.01

        return NDVI

    # Calculate NDSI
    def calculateNDSI(self, landsat):
        NDSI     = (landsat[self.bandID[1]] - landsat[self.bandID[4]])/(landsat[self.bandID[1]] + landsat[self.bandID[4]])
        NDSI[(landsat[self.bandID[1]] + landsat[self.bandID[4]])== 0] = 0.01

        return NDSI

    # Identify the cloud pixels, snow pixels, water pixels, clear land pixels, and potential shadow pixels
    def potential_cloud_shadow_snow_mask(self, landsat):
        DIM = landsat[0].shape              # dimensions of Landsat scene

        # cirrus band probability for Landsat 8
        if self.scene != "Landsat 8":   Thin_prob = 0
        else:                           Thin_prob = (10**4) * landsat[-2] / 400

        Cloud   = np.zeros(DIM,'uint8') # Cloud mask
        Snow    = np.zeros(DIM,'uint8') # Snow mask
        WT      = np.zeros(DIM,'uint8') # Water mask
        Shadow  = np.zeros(DIM,'uint8') # Shadow mask

        # multiplicative factor for Landsat scene
        if self.albedo == "True":       mulFactor = 10**4
        else:                           mulFactor = 1

        # assignment of Landsat bands
        data1   = mulFactor * landsat[self.bandID[0]]
        data2   = mulFactor * landsat[self.bandID[1]]
        data3   = mulFactor * landsat[self.bandID[2]]
        data4   = mulFactor * landsat[self.bandID[3]]
        data5   = mulFactor * landsat[self.bandID[4]]
        data6   = mulFactor * landsat[self.bandID[5]]

        # brightness temperature
        Temp    = landsat[-1]

        # overlapping region of thermal band and multispectral bands
        mask    = np.greater(Temp, -9999)

        # saturation test on visible bands
        satu_Bv = np.logical_or(np.less(data1, 0),np.logical_or(np.less(data2, 0),np.less(data3, 0)))

        ####### PASS 1 : Potential Cloud / Cloud Shadow / Snow Layer Detection #######
        ####### POTENTIAL CLOUD PIXELS #######

        ## 1. Basic Test ##

        pCloudPixels = np.logical_and(np.logical_and(np.less(self.NDSI, 0.8), np.less(self.NDVI, 0.8)),\
                       np.logical_and(np.greater(data6, 300),np.less(Temp, 2700)))

        ## 2. Snow Test ##

        # OR condition used to include all pixels between thin / thick clouds
        snowCondition = np.logical_or(np.logical_and(np.greater(self.NDSI, 0.15),np.logical_and(np.greater(data4, 1100),\
                        np.greater(data2, 1000))),np.less(Temp, 400))

        Snow[snowCondition] = 1

        ## 3. Water Test ##

        water_Condition = np.logical_or(np.logical_and(np.less(self.NDVI, 0.01), np.less(data4, 1100)), \
                          np.logical_and(np.logical_and(np.less(self.NDVI, 0.1), np.greater(self.NDVI,0)),np.less(data4, 500)))

        WT[water_Condition] = 1
        WT[mask == 0] = 255

        ## 4. Whiteness Test ##

        visimean =  (data1 + data2 + data3)  / 3
        whiteness = (np.abs(data1 - visimean) + np.abs(data2 - visimean) + np.abs(data3 - visimean)) / visimean

        # release memory
        del visimean

        # update potential cloud pixels
        whiteness[satu_Bv] = 0
        pCloudPixels   = np.logical_and(pCloudPixels, np.less(whiteness , 0.7))

        ## 5. HOT Test ##

        HOT = (np.logical_or(np.greater((data1 - 0.5 * data3 - 800) , 0), satu_Bv))
        pCloudPixels   = np.logical_and(pCloudPixels, HOT)

        # release memory
        del HOT

        ## 6. SWIRNIR Test ##

        pCloudPixels   = np.logical_and(pCloudPixels, np.greater((data4 / data5) , 0.75))

        ## 7. Cirrus Test ##

        pCloudPixels   = np.logical_or(pCloudPixels, np.greater(Thin_prob , 0.25))

        # Percentile Constants
        l_Percentile = 0.175            # low percent
        h_Percentile = 1 - l_Percentile # high percent

        ## Temperature and Snow Test ##

        clearPixels  = np.logical_and(pCloudPixels == False, mask == 1)
        ptm          = 100 * clearPixels.sum() / mask.sum()
        landPixels   = np.logical_and(clearPixels, WT == False)
        waterPixels  = np.logical_and(clearPixels, WT == True)
        lndptm       = 100 * landPixels.sum() / mask.sum()

        # no thermal test => meanless for snow detection

        if ptm <= 0.001:          # all cloud no clear pixel to move to pass 2

            Cloud[pCloudPixels==True]   = 1
            Cloud[np.logical_not(mask)] = 0
            Shadow[Cloud == 0]          = 1
            Temp                        = -1
            tempLow                     = -1
            tempHigh                    = -1

        else:

            if lndptm >= 0.1:       F_temp = Temp[landPixels]
            else:                   F_temp = Temp[clearPixels]

            ## WATER PROBABILITY ##
            ## 1. Temperature Test ##

            F_wtemp = Temp[waterPixels]

            if len(F_wtemp) == 0:   t_wtemp = 0
            else:                   t_wtemp = scipy.stats.scoreatpercentile(F_wtemp, 100 * h_Percentile)

            wTemp_prob = (t_wtemp - Temp) / 400
            wTemp_prob[np.less(wTemp_prob, 0)] = 0

            ## 2. Brightness Test ##

            tempBright      = 1100
            Brightness_prob = np.clip((data5 / tempBright), 0, 1)

            cloudProb = .125    # Change Cloud Proability to 22.5 %

            ## FINAL WATER PROBABILITY ##

            wfinal_prob = 100 * wTemp_prob * Brightness_prob + 100 * Thin_prob                                    # cloud over water probability
            wclr_max    = scipy.stats.scoreatpercentile(wfinal_prob[waterPixels], 100 * h_Percentile) + cloudProb # dynamic threshold (water)
            #wclr_max   = 50    # old threshold for water fixed

            # release memory
            del wTemp_prob
            del Brightness_prob

            ## LAND PROBABILITY ##
            ## 1. Temperature Test ##

            t_buffer = 4 * 100

            if len(F_temp) != 0:

                tempLow     = scipy.stats.scoreatpercentile(F_temp, 100 * l_Percentile) # 0.175 percentile background temperature
                tempHigh    = scipy.stats.scoreatpercentile(F_temp, 100 * h_Percentile) # 0.825 percentile background temperature

            else:   tempLow, tempHigh = 0 , 0

            t_tempL     = tempLow - t_buffer
            t_tempH     = tempHigh + t_buffer
            Temp_l      = t_tempH - t_tempL
            Temp_prob   = (t_tempH - Temp) / Temp_l

            Temp_prob[np.less(Temp_prob,0)] = 0

            self.NDSI[np.logical_and(np.less(data2,0), np.less(self.NDSI,0))]    = 0
            self.NDVI[np.logical_and(np.less(data3,0), np.greater(self.NDSI,0))] = 0

            Vari_prob= 1 - np.maximum(np.maximum(np.abs(self.NDSI), np.abs(self.NDVI)), whiteness)

            # release memory
            del whiteness

            ## FINAL LAND PROBABILITY ##

            final_prob = 100 * Temp_prob * Vari_prob + 100 * Thin_prob                          # cloud over land probability
            clr_max    = scipy.stats.scoreatpercentile(final_prob[landPixels], 100 * h_Percentile) + cloudProb # dynamic threshold (land)

            # release memory
            del Vari_prob
            del Temp_prob
            del Thin_prob

            ####### POTENTIAL CLOUD LAYER #######

            # Condition 1   : (idplcd & (final_prob > clr_max) & (WT == 0))
            # Condition 2   : (idplcd & (wfinal_prob > wclr_max) & (WT == 1))
            # Condition 3   : (Temp < t_templ - 3500)
            # Condition 4   : (final_prob > 99.0) & (WT == 0) Small clouds don't get masked out

            condition1  = np.logical_and(np.logical_and(pCloudPixels, np.greater(final_prob, clr_max)),np.logical_not(WT))
            condition2  = np.logical_and(np.logical_and(pCloudPixels, np.greater(wfinal_prob, wclr_max)), WT)
            condition3  = np.less(Temp, tempLow - 3500)
            condition4  = np.logical_and(np.greater(final_prob,99.0),np.logical_not(WT))

            pCloudLayer = np.logical_or(np.logical_or(condition1,condition2), condition3)

            Cloud[pCloudLayer] = 1  # potential cloud mask

            # release memory
            del final_prob
            del wfinal_prob
            del pCloudLayer

            ####### POTENTIAL CLOUD SHADOW LAYER #######
            ## 1. Band 4 Flood Fill ##

            nir = data4.astype('float32')
            backg_B4 = scipy.stats.scoreatpercentile(nir[landPixels], 100.0 * l_Percentile)  # estimate background from Band 4
            nir[np.logical_not(mask)] = backg_B4
            nir = self.imfill(nir)
            nir = nir - data4

            ## 2. Band 5 Flood Fill ##

            swir = data5.astype('float32')
            backg_B5 = scipy.stats.scoreatpercentile(swir[landPixels], 100.0 * l_Percentile)
            swir[np.logical_not(mask)] = backg_B5
            swir = self.imfill(swir)    # fill in regional minimum Band 5
            swir = swir - data5

            shadow_prob = np.minimum(nir, swir) # Shadow Probability

            # release remory
            del nir
            del swir

            Shadow[np.greater(shadow_prob , 200)] = 1

            # release remory
            del shadow_prob

        WT[np.logical_and(WT ==1 ,Cloud == 0)] = 1
        Cloud               = Cloud.astype("uint8")
        Cloud[mask == 0]    = 255
        Shadow[mask == 0]   = 255

        ####### END OF PASS 1 #######

        ####### PASS 2 : Object Matching for Cloud Shadow Detection #######
        maskOutput = self.object_cloud_shadow_match(ptm, Temp, tempLow, tempHigh, WT, Snow, Cloud, Shadow, DIM)

        return maskOutput

    # Object matching of Cloud Shadow and dilation of mask
    def object_cloud_shadow_match(self, ptm, Temp, tempLow, tempHigh, Water, Snow, Cloud, Shadow, DIM):

        cloudPixel, shadowPixel, snowPixel= 3, 3, 3      # dilation 3 neighbouring pixels surrounding

        maskOutput    = np.zeros(DIM, 'uint8')           # final output of fmask

        sun_ele_rad   = math.radians(self.sunEle)        # solar elevation angle
        sun_azi_rad   = math.radians(self.sunAzi - 90.0) # solar azimuth angle

        cellSize      = self.resolu[0]
        height        = DIM[0]
        width         = DIM[1]

        # potential cloud & shadow layer
        cloudTest   = np.zeros(DIM, 'uint8')
        shadowTest  = np.zeros(DIM, 'uint8')

        # matched cloud & shadow layer
        shadowCal    = np.zeros(DIM, 'uint8')
        cloudCal     = np.zeros(DIM, 'uint8')
        boundaryTest = np.zeros(DIM, 'uint8')

        shadowTest[Shadow == 1] = 1  # Potential Cloud Shadow Layer

        del Shadow   # release memory

        boundaryTest[Cloud < 255] = 1     # boundarylayer
        cloudTest[Cloud == 1]     = 1     # Potential Cloud layer

        del Cloud   # release memory

        revised_ptm = np.sum(cloudTest) / np.sum(boundaryTest)

        # full scene covered in cloud return everything as masked
        if ptm <= 0.1 or revised_ptm >= 0.90:

            cloudCal[cloudTest == True]     = 1
            shadowCal[cloudTest == False]  = 1
            similar_num                     = -1

        else:

            ####### CLOUD SHADOW LAYER DETECTION #######

            # constants for object matching

            Tsimilar    = 0.30
            Tbuffer     = 0.95  # threshold for matching buffering
            max_similar = 0.95  # max similarity threshold
            num_cldoj   = 9     # minimum matched cloud object (pixels) - {3,9}
            num_pix     = 3     # number of inward pixes (90m) for cloud base temperature

            # enviromental lapse rate 6.5 degrees/km
            # dry adiabatic lapse rate 9.8 degrees/km

            rate_elapse = 6.5 # degrees/km
            rate_dlapse = 9.8 # degrees/km

            i_step = 2 * float(cellSize) * math.tan(sun_ele_rad) # move 2 pixel at a time

            if (i_step < (2 * cellSize)):   i_step = 2 *cellSize    # make i_step = 2 for polar large solar zenith angle case

            # get moving direction

            (rows,cols)= np.nonzero(boundaryTest)
            (y_ul,num) = (rows.min(), rows.argmin())
            x_ul = cols[num]

            (y_lr,num) = (rows.max(), rows.argmax())
            x_lr = cols[num]

            (x_ll,num) = (cols.min(), cols.argmin())
            y_ll = rows[num]

            (x_ur,num) = (cols.max(), cols.argmax())
            y_ur = rows[num]

            # view angle geometry
            (A, B, C, omiga_par, omiga_per) = self.viewgeo(float(x_ul), float(y_ul), float(x_ur), float(y_ur), float(x_ll), float(y_ll), float(x_lr), float(y_lr))

            # segmentation of each cloud object
            (segm_cloud_init, segm_cloud_init_features) = scipy.ndimage.measurements.label(cloudTest, scipy.ndimage.morphology.generate_binary_structure(2,2))

            morphology.remove_small_objects(segm_cloud_init, num_cldoj, in_place=True) # filter out each cloud object with < than 9 pixels (num_cldobj)
            segm_cloud, fm, invm = segmentation.relabel_sequential(segm_cloud_init)

            num = np.max(segm_cloud)

            cloudProp = measure.regionprops(segm_cloud) # properties of each cloud object

            similar_num = np.zeros(num) # cloud shadow match similarity

            # iterate cloud object to obtain cloud base height {min, max} for cloud shadow detection
            for cloud_type in cloudProp:

                cloudArea  = cloud_type['Area']
                cloudLabel = cloud_type['Label']
                num_pixels = cloudArea

                XY_type     = np.zeros((2,num_pixels), dtype='uint32')     # moving cloud xys
                tmp_XY_type = np.zeros((2,num_pixels), dtype='uint32')     # record the max threshold moving cloud xys
                tmp_xys     = np.zeros((2,num_pixels))                     # corrected for view angle xys

                cloudCoord  = (cloud_type['Coordinates'][:,0],cloud_type['Coordinates'][:,1]) # cloud pixellist coordinates (x,y)
                tempObj     = Temp[cloudCoord]   # temperature of the cloud object
                r_obj       = math.sqrt(cloudArea / 2 *math.pi)    # used for getting influenced cloud BT

                num_pix     = 8
                pct_obj     = math.pow(r_obj - num_pix, 2) / math.pow(r_obj, 2)
                pct_obj     = np.minimum(pct_obj, 1) # pct of edge pixel should be less than 1
                t_obj       = scipy.stats.mstats.mquantiles(tempObj, pct_obj)

                # put the edge of the cloud the same value as t_obj
                tempObj[tempObj > t_obj] = t_obj

                Max_cl_height = 12000   # Max cloud base height (m)
                Min_cl_height = 200     # Min cloud base height (m)

                # refine cloud height range (m)
                # Min_cl_height = max(Min_cl_height, int(10 *(tempLow - 400 - t_obj) / rate_dlapse)) # Removed from Matlab code
                # Max_cl_height = min(Max_cl_height, int(10 *(tempHigh + 400 - t_obj)))              # Removed from Matlab code

                # height and similarity variable
                record_h      = 0.0
                record_thresh = 0.0

                # iterate in height (m)
                for base_h in np.arange(Min_cl_height, Max_cl_height, i_step):
                    # Get the true postion of the cloud. calculate cloud DEM with initial base height

                    h = base_h  # Equation changed in Matlab code
                   # h = (10 * (t_obj - tempObj) / rate_elapse + base_h) # Original equation

                    tmp_xys[1,:], tmp_xys[0,:] = self.mat_truecloud(cloudCoord[1], cloudCoord[0], h, A, B, C, omiga_par, omiga_per) # Return new (x,y) co-ordinates

                    i_xy = h / (cellSize * math.tan(sun_ele_rad))

                    if self.sunAzi < 180:

                        XY_type[1,:] = np.round(tmp_xys[1,:] - i_xy * math.cos(sun_azi_rad)) # X is for j, 1
                        XY_type[0,:] = np.round(tmp_xys[0,:] - i_xy * math.sin(sun_azi_rad)) # Y is for i, 0

                    else:

                        XY_type[1,:] = np.round(tmp_xys[1,:] + i_xy * math.cos(sun_azi_rad)) # X is for j, 1
                        XY_type[0,:] = np.round(tmp_xys[0,:] + i_xy * math.sin(sun_azi_rad)) # Y is for i, 0

                    tmp_j = XY_type[1,:] # column
                    tmp_i = XY_type[0,:] # row

                    out_id = (tmp_i < 0) | (tmp_i >=  height) | (tmp_j < 0) | (tmp_j >=  width) # ID out of scene
                    out_all = np.sum(out_id)

                    tmp_ii = tmp_i[out_id == 0]
                    tmp_jj = tmp_j[out_id == 0]

                    tmp_id = [tmp_ii, tmp_jj]

                    # matched ID - exclude original cloud
                    match_id    = (boundaryTest[tmp_id] == 0) | ((segm_cloud[tmp_id] != cloudLabel) & ((cloudTest[tmp_id] > 0) | (shadowTest[tmp_id] == 1)))
                    matched_all = np.sum(match_id) + out_all

                    # total pixel ID - exclude original cloud
                    total_id  = segm_cloud[tmp_id] !=cloudLabel
                    total_all = np.sum(total_id) + out_all

                    ####### SIMILARITY THRESHOLD CALCULATION #######

                    thresh_match = np.float32(matched_all) / total_all

                    if (thresh_match >= (Tbuffer * record_thresh)) and (base_h < (Max_cl_height - i_step)) and (record_thresh < max_similar):

                        if thresh_match > record_thresh:
                            record_thresh = thresh_match
                            record_h = h

                    elif record_thresh > Tsimilar:

                        similar_num[cloudLabel -1] = record_thresh
                        i_vir = record_h / (cellSize * math.tan(sun_ele_rad))

                        if self.sunAzi < 180:

                            tmp_XY_type[1,:] = np.round(tmp_xys[1,:] - i_vir * math.cos(sun_azi_rad)) # X is for col j,2
                            tmp_XY_type[0,:] = np.round(tmp_xys[0,:] - i_vir * math.sin(sun_azi_rad)) # Y is for row i,1

                        else:

                            tmp_XY_type[1,:] = np.round(tmp_xys[1,:] + i_vir * math.cos(sun_azi_rad)) # X is for col j,2
                            tmp_XY_type[0,:] = np.round(tmp_xys[0,:] + i_vir * math.sin(sun_azi_rad)) # Y is for row i,1

                        tmp_scol = tmp_XY_type[1,:]
                        tmp_srow = tmp_XY_type[0,:]

                        # put data within range
                        tmp_srow[tmp_srow < 0]       = 0
                        tmp_srow[tmp_srow >= height] = height - 1
                        tmp_scol[tmp_scol < 0]       = 0
                        tmp_scol[tmp_scol >= width]  = width - 1

                        tmp_sid = [tmp_srow, tmp_scol]
                        shadowCal[tmp_sid] = 1

                        break
                    else:
                        record_thresh = 0.0

            # Dilation of pixels in neighbourhood of 3
            SEc  = cloudPixel
            SEc  = np.ones((SEc, SEc), 'uint8')
            SEs  = shadowPixel
            SEs  = np.ones((SEs, SEs), 'uint8')
            SEsn = snowPixel
            SEsn = np.ones((SEsn, SEsn), 'uint8')

            shadowCal = scipy.ndimage.morphology.binary_dilation(shadowCal, structure=SEs) # dilate Shadow layer
            segm_cloud_tmp = (segm_cloud != 0)
            cloudCal = scipy.ndimage.morphology.binary_dilation(segm_cloud_tmp, structure=SEc) # dilate Cloud layer
            Snow = scipy.ndimage.morphology.binary_dilation(Snow, structure=SEsn) # dilate Snow layer

        maskOutput[boundaryTest == 0] = 255

        if self.mode == "Only Snow":        maskOutput[Snow == 1] = 1
        elif self.mode == "Cloud + Shadow": maskOutput[np.logical_or(shadowCal == 1, cloudCal == 1)] = 1
        elif self.mode == "Only Cloud":     maskOutput[cloudCal == 1] = 1
        else:                               maskOutput[np.logical_or(np.logical_or(shadowCal == 1, cloudCal == 1),Snow == 1)] = 1

        return maskOutput

    # viewgeo - Calculate the geometric parameters needed for the cloud/shadow match
    def viewgeo(self, x_ul, y_ul, x_ur, y_ur, x_ll, y_ll, x_lr, y_lr):

        x_u = (x_ul + x_ur) / 2
        x_l = (x_ll + x_lr) / 2
        y_u = (y_ul + y_ur) / 2
        y_l = (y_ll + y_lr) / 2

        # get k of the upper left and right points
        if (x_ul != x_ur):     K_ulr = (y_ul - y_ur) /  (x_ul - x_ur)
        else:                  K_ulr = 0.0

        # get k of the lower left and right points
        if (x_ll != x_lr):     K_llr = (y_ll - y_lr) /  (x_ll - x_lr)
        else:                  K_llr = 0.0

        K_aver = (K_ulr + K_llr) / 2
        omiga_par = math.atan(K_aver) # get the angle of parallel lines k (in pi)

        A = y_u - y_l
        B = x_l - x_u
        C = y_l * x_u - x_l * y_u

        omiga_per = math.atan(B / A) # get the angle which is perpendicular to the trace line

        return (A, B, C, omiga_par, omiga_per)

    # mat_truecloud - Calculate shadow pixel locations of a true cloud segment
    def mat_truecloud(self, x, y, h, A, B, C, omiga_par, omiga_per):

        H         = 705000                      # average Landsat height (m)
        dist      = (A * x + B * y + C) / math.sqrt(A * A + B * B)
        dist_par  = dist / math.cos(omiga_per - omiga_par)
        dist_move = dist_par * h / H            # cloud move distance (m)
        delt_x    = dist_move * math.cos(omiga_par)
        delt_y    = dist_move * math.sin(omiga_par)

        x_new     = x + delt_x              # new x, j
        y_new     = y + delt_y              # new y, i

        return (x_new, y_new)

    # imfill - Flood-fill transformation : Fills image regions and holes
    def imfill(self, band):

        seed = band.copy()
        seed[1:-1, 1:-1] = band.max()   # Borders masked with maximum value of image
        filled = morphology.reconstruction(seed, band, method='erosion') # Fill the holes - Equivalent to imfill

        return filled

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

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
