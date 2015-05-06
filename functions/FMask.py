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
                'domain': ('Only Cloud' , 'Cloud + Shadow',  'Only Snow'),
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

        kwargs['output_info']['pixelType'] = 'f4'       # Change to 8 bit output i1 (0 to 255)
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
        output       = self.potential_cloud_shadow_snow_mask(landsat)

        for band in xrange(landsat.shape[0]):
            fmask[band]     = np.where(output  , 255 , landsat[band])

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
        self.scene = scene
        self.mode = mode
        self.albedo = albedo
        self.sunEle = sunElevation
        self.sunAzi = sunAzimuth
        self.resolu = resolu

        if scene == "Landsat 8":
            self.k1 , self.k2       = 774.89 , 1321.08          # Thermal Conversion Constants
            self.lmax , self.lmin   = 22.00180 ,  0.10033       # Radiance Thermal Bands Min_Max
            self.dn                 = 65534                     # Digital Number Limit
            self.bandID             = [1, 2, 3, 4, 5, 6, 7, 8]  # Band IDs

        elif scene == "Landsat 7":
            self.k1, self.k2        = 666.09 , 1282.71
            self.lmax , self.lmin   = 17.04 , 0.0
            self.dn                 = 244
            self.bandID             = [0, 1, 2, 3, 4, 5, 6]

        else:
            self.k1, self.k2        = 607.76 , 1260.56
            self.lmax , self.lmin   = 15.303 , 1.238
            self.dn                 = 244
            self.bandID             = [0, 1, 2, 3, 4, 5, 6]


    # Calculate Brightness Temperature from Thermal Band
    def convertScene(self, landsat):
        landsat[-1] = ((self.lmax - self.lmin) / self.dn) * landsat[-1] + self.lmin
        landsat[-1] = 100 * (((self.k2/np.log((self.k1/landsat[-1])+1))) - 273.15)   # Convert to Celsius

        if self.albedo == "False":                                                   # Normalized calculated TOA values of Landsat Scene
            for band in xrange(0, landsat.shape[0]-1):
                landsat[band] /= (10**4)

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
        dim = landsat[0].shape              # dimensions of the scene

        if self.scene != "Landsat 8":       # cirrus band probability for Landsat 8
            Thin_prob   = 0
        else:
            Thin_prob   = 10000* landsat[-2] / 400

        Cloud   = np.zeros(dim,'uint8') # cloud mask
        Snow    = np.zeros(dim,'uint8') # Snow mask
        WT      = np.zeros(dim,'uint8') # Water mask
        Shadow  = np.zeros(dim,'uint8') # shadow mask

        # assignment of Landsat bands
        data1   = 10000 * landsat[self.bandID[0]]
        data2   = 10000 * landsat[self.bandID[1]]
        data3   = 10000 * landsat[self.bandID[2]]
        data4   = 10000 * landsat[self.bandID[3]]
        data5   = 10000 * landsat[self.bandID[4]]
        data6   = 10000 * landsat[self.bandID[5]]

        # brightness temperature
        Temp    = landsat[-1]

        # only work on overlapping region
        mask    = np.greater(Temp, -9999)

        # saturation test
        satu_Bv = np.logical_or(np.less(data1, 0),np.logical_or(np.less(data2, 0),np.less(data3, 0)))

        ## Basic cloud test ##
        idplcd = np.logical_and(np.logical_and(np.less(self.NDSI, 0.8), np.less(self.NDVI, 0.8)),\
                 np.logical_and(np.greater(data6, 300),np.less(Temp, 2700)))


        ## Snow test ##
        # OR condition used to include all pixels between thin / thick clouds
        snow_Condition = np.logical_or(np.logical_and(np.greater(self.NDSI, 0.15),np.logical_and(np.greater(data4, 1100),\
                         np.greater(data2, 1000))),np.less(Temp, 400))

        Snow[snow_Condition] = 1

        ## Water test ##
        water_Condition = np.logical_or(np.logical_and(np.less(self.NDVI, 0.01), np.less(data4, 1100)), \
                          np.logical_and(np.logical_and(np.less(self.NDVI, 0.1), np.greater(self.NDVI,0)),np.less(data4, 500)))

        WT[water_Condition] = 1
        WT[mask == 0] = 255

        ## Whiteness test ##
        visimean =  (data1 + data2 + data3)  / 3
        whiteness = (np.abs(data1 - visimean) + np.abs(data2 - visimean) + np.abs(data3 - visimean)) / visimean

        # release memory
        del visimean

        # update idplcd
        whiteness[satu_Bv] = 0
        idplcd = np.logical_and(idplcd, np.less(whiteness , 0.7))

        ## Haze test ##
        HOT = (np.logical_or(np.greater((data1 - 0.5 * data3 - 800) , 0), satu_Bv))
        idplcd = np.logical_and(idplcd, HOT)

        # release memory
        del HOT

        ## SWIRNIR test ##
        idplcd = np.logical_and(idplcd, np.greater((data4 / data5) , 0.75))

        ## Cirrus test ##
        idplcd = np.logical_or(idplcd, np.greater(Thin_prob , 0.25))


        ## Percentile Constants ##
        l_pt = 0.175 # low percent
        h_pt = 1 - l_pt # high percent

        ## Temperature & Snow test ##
        idclr = np.logical_and(idplcd == False, mask == 1)
        ptm   = 100 * idclr.sum() / mask.sum()
        idlnd = np.logical_and(idclr, WT == False)
        idwt  = np.logical_and(idclr, WT == True)
        lndptm = 100 * idlnd.sum() / mask.sum()

        if ptm <= 0.001:          # scene comprises of all clouds
            Cloud[idplcd] = 1
            Cloud[~(mask)] = 0
            Shadow[Cloud == 0] = 1
            Temp = -1
            t_templ = -1
            t_temph = -1

        else:
            if lndptm >= 0.1:
                F_temp = Temp[idlnd]
            else:
                F_temp = Temp[idclr]

        # Water Probability
            # Temperature Test
            F_wtemp = Temp[idwt]

            if len(F_wtemp) == 0:
                t_wtemp = 0
            else:
                t_wtemp = scipy.stats.scoreatpercentile(F_wtemp, 100 * h_pt)

            wTemp_prob = (t_wtemp - Temp) / 400
            wTemp_prob[np.less(wTemp_prob, 0)] = 0

            # Brightness Test
            t_bright = 1100
            Brightness_prob = data5 / t_bright
            Brightness_prob = np.clip(Brightness_prob, 0, 1)

            # CHANGE CLOUD PROBABILITY TO 22.5 %
            cldprob = .125

            # Final Water Probability
            wfinal_prob = 100 * wTemp_prob * Brightness_prob + 100 * Thin_prob # cloud over water probability
            wclr_max    = scipy.stats.scoreatpercentile(wfinal_prob[idwt], 100 * h_pt) + cldprob # dynamic threshold (land)

            # Old Threshold for Water fixed
            #wclr_max   = 50

            # release memory
            del wTemp_prob
            del Brightness_prob

            # Temperature test for Land
            t_buffer = 4 * 100
            if len(F_temp) != 0:
                # 0.175 percentile background temperature
                t_templ = scipy.stats.scoreatpercentile(F_temp, 100 * l_pt)

                # 0.825 percentile background temperature
                t_temph = scipy.stats.scoreatpercentile(F_temp, 100 * h_pt)

            else:
                t_templ = 0
                t_temph = 0

            t_tempL = t_templ - t_buffer
            t_tempH = t_temph + t_buffer
            Temp_l = t_tempH - t_tempL
            Temp_prob = (t_tempH - Temp) / Temp_l

            Temp_prob[np.less(Temp_prob,0)] = 0

            self.NDSI[np.logical_and(np.less(data2,0), np.less(self.NDSI,0))] = 0
            self.NDVI[np.logical_and(np.less(data3,0), np.greater(self.NDSI,0))] = 0

            Vari_prob= 1 - np.maximum(np.maximum(np.abs(self.NDSI), np.abs(self.NDVI)), whiteness)

            # release memory
            del whiteness

            # Final Land Probability
            final_prob = 100 * Temp_prob * Vari_prob + 100 * Thin_prob                          # cloud over land probability
            clr_max    = scipy.stats.scoreatpercentile(final_prob[idlnd], 100 * h_pt) + cldprob # dynamic threshold (land)

            # release memory
            del Vari_prob
            del Temp_prob
            del Thin_prob

            # Condition 1   : (idplcd & (final_prob > clr_max) & (WT == 0))
            # Condition 2   : (idplcd & (wfinal_prob > wclr_max) & (WT == 1))
            # Condition 3   : (final_prob > 99.0) & (WT == 0) Results comes out to be incorrect
            # Condition 4   : (Temp < t_templ - 3500)

            condition1 = np.logical_and(np.logical_and(idplcd, np.greater(final_prob, clr_max)),np.logical_not(WT))
            condition2 = np.logical_and(np.logical_and(idplcd, np.greater(wfinal_prob, wclr_max)), WT)
            condition3 = np.less(Temp, t_templ - 3500)

            id_final_cld = np.logical_or(np.logical_or(condition1,condition2), condition3)

            # potential cloud mask
            Cloud[id_final_cld] = 1

            # release memory
            del final_prob
            del wfinal_prob
            del id_final_cld

            ## Potential Cloud Shadow Mask
            # band 4 flood fill
            nir = data4.astype('float32')

            # estimating background (land) Band 4 ref
            backg_B4 = scipy.stats.scoreatpercentile(nir[idlnd], 100.0 * l_pt)
            nir[np.logical_not(mask)] = backg_B4

            # fill in regional minimum Band 4 ref
            nir = self.imfill(nir)
            nir = nir - data4

            # band 5 flood fill
            swir = data5.astype('float32')

            # estimating background (land) Band 4 ref
            backg_B5 = scipy.stats.scoreatpercentile(swir[idlnd], 100.0 * l_pt)
            swir[np.logical_not(mask)] = backg_B5

            # fill in regional minimum Band 5 ref
            swir = self.imfill(swir)
            swir = swir - data5

            shadow_prob = np.minimum(nir, swir)

            # release remory
            del nir
            del swir

            Shadow[np.greater(shadow_prob , 200)] = 1

            # release remory
            del shadow_prob

        WT[np.logical_and(WT,Cloud == 0)] = 1
        Cloud = Cloud.astype("uint8")
        Cloud[mask == 0] = 255
        Shadow[mask ==0] =255

        output = self.object_cloud_shadow_match(ptm, Temp, t_templ, t_temph, WT, Snow, Cloud, Shadow, dim, 3 ,3, 3)
        return output

    def object_cloud_shadow_match(self, ptm,Temp,t_templ,t_temph,Water,Snow,plcim,plsim,ijDim,cldpix,sdpix,snpix):
        # solar elevation angle
        sun_ele_rad = math.radians(self.sunEle)

        # solar azimuth angle
        Sun_tazi     = self.sunAzi - 90.0
        sun_tazi_rad = math.radians(Sun_tazi)

        sub_size     = self.resolu[0]
        win_height   = ijDim[0]
        win_width    = ijDim[1]

        # potential cloud & shadow layer
        cloud_test   = np.zeros(ijDim,'uint8')
        shadow_test  = np.zeros(ijDim,'uint8')

        # matched cloud & shadow layer
        shadow_cal   = np.zeros(ijDim,'uint8')
        cloud_cal    = np.zeros(ijDim,'uint8')
        boundary_test = np.zeros(ijDim,'uint8')
        shadow_test[plsim == 1] = 1 #plshadow layer

        # release memory
        del plsim

        boundary_test[plcim < 255] = 1 # boundary layer
        cloud_test[plcim == 1] = 1    # plcloud layer

        # release memory
        del plcim

        revised_ptm = np.sum(cloud_test) / np.sum(boundary_test)

        # full scene covered in cloud return everything as masked
        if ptm <= 0.1 or revised_ptm >= 0.90:
            cloud_cal[cloud_test == True] = 1
            shadow_cal[cloud_test == False] = 1
            similar_num = -1

        else:
            # Shadow Matching
            Tsimilar    = 0.30
            Tbuffer     = 0.95  # threshold for matching buffering
            max_similar = 0.95  # max similarity threshold
            num_cldoj   = 9     # minimum matched cloud object (pixels)
            num_pix     = 3     # number of inward pixes (90m) for cloud base temperature

            # enviromental lapse rate 6.5 degrees/km
            # dry adiabatic lapse rate 9.8 degrees/km

            rate_elapse = 6.5 # degrees/km
            rate_dlapse = 9.8 # degrees/km

            i_step = 2 * float(sub_size) * math.tan(sun_ele_rad)

            if (i_step < (2 * sub_size)):
                i_step = 2 * sub_size

            # get moving direction
            (rows,cols)= np.nonzero(boundary_test)
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

            # Segmentation of each cloud
            (segm_cloud_init,segm_cloud_init_features) = scipy.ndimage.measurements.label(cloud_test, scipy.ndimage.morphology.generate_binary_structure(2,2))

            # Filter out each cloud object with < than 9 pixels (num_cldobj)
            morphology.remove_small_objects(segm_cloud_init, num_cldoj, in_place=True)
            segm_cloud, fw, inv = segmentation.relabel_sequential(segm_cloud_init)

            num = np.max(segm_cloud)

            # Access properties of each cloud label
            s = measure.regionprops(segm_cloud)

            # cloud shadow match similarity
            similar_num = np.zeros(num)

            # Loop through each cloud objects
            for cloud_type in s:
                cld_area  = cloud_type['Area']
                cld_label = cloud_type['Label']

                num_pixels = cld_area

                # moving cloud xys
                XY_type = np.zeros((2,num_pixels), dtype='uint32')

                # record the max threshold moving cloud xys
                tmp_XY_type = np.zeros((2,num_pixels), dtype='uint32')

                # corrected for view angle xys
                tmp_xys = np.zeros((2,num_pixels)) # Leave as float for the time being

                # record this original ids
                orin_cid = (cloud_type['Coordinates'][:,0],cloud_type['Coordinates'][:,1])

                # Temperature of the cloud object
                temp_obj = Temp[orin_cid]

                # assume object is round r_obj is radium of object
                r_obj    = math.sqrt(cld_area / math.pi)

                # number of inward pixes for correct temperature
                # num_pix = 25
                pct_obj = math.pow(r_obj - num_pix, 2) / math.pow(r_obj, 2)
                pct_obj = np.minimum(pct_obj, 1) # pct of edge pixel should be less than 1
                t_obj   = scipy.stats.mstats.mquantiles(temp_obj, pct_obj)

                # put the edge of the cloud the same value as t_obj
                temp_obj[temp_obj > t_obj] = t_obj

                Max_cl_height = 12000   # Max cloud base height (m)
                Min_cl_height = 200     # Min cloud base height (m)

                # refine cloud height range (m)
                Min_cl_height = max(Min_cl_height, 10 *(t_templ - 400 - t_obj) / rate_dlapse)
                Max_cl_height = min(Max_cl_height, 10 *(t_temph + 400 - t_obj))

                # initialize height and similarity info
                record_h      = 0.0
                record_thresh = 0.0

                for base_h in np.arange(Min_cl_height, Max_cl_height, i_step): # iterate in height (m)
                    # Get the true postion of the cloud
                    # calculate cloud DEM with initial base height
                    h = (10 * (t_obj - temp_obj) / rate_elapse + base_h)
                    tmp_xys[1,:], tmp_xys[0,:] = self.mat_truecloud(orin_cid[1], orin_cid[0], h, A, B, C, omiga_par, omiga_per) # Return new (x,y) co-ordinates

                    i_xy = h / (sub_size * math.tan(sun_ele_rad))

                    if self.sunAzi < 180:
                        XY_type[1,:] = np.round(tmp_xys[1,:] - i_xy * math.cos(sun_tazi_rad)) # X is for j,1
                        XY_type[0,:] = np.round(tmp_xys[0,:] - i_xy * math.sin(sun_tazi_rad)) # Y is for i,0
                    else:
                        XY_type[1,:] = np.round(tmp_xys[1,:] + i_xy * math.cos(sun_tazi_rad)) # X is for j,1
                        XY_type[0,:] = np.round(tmp_xys[0,:] + i_xy * math.sin(sun_tazi_rad)) # Y is for i,0

                    tmp_j = XY_type[1,:] # col
                    tmp_i = XY_type[0,:] # row

                    # the id that is out of the image
                    out_id = (tmp_i < 0) | (tmp_i >= win_height) | (tmp_j < 0) | (tmp_j >= win_width)
                    out_all = np.sum(out_id)

                    tmp_ii = tmp_i[out_id == 0]
                    tmp_jj = tmp_j[out_id == 0]

                    tmp_id = [tmp_ii, tmp_jj]

                    # the id that is matched (exclude original cloud)
                    match_id    = (boundary_test[tmp_id] == 0) | ((segm_cloud[tmp_id] != cld_label) & ((cloud_test[tmp_id] > 0) | (shadow_test[tmp_id] == 1)))
                    matched_all = np.sum(match_id) + out_all

                    # the id that is the total pixel (exclude original cloud)
                    total_id  = segm_cloud[tmp_id] != cld_label
                    total_all = np.sum(total_id) + out_all

                    thresh_match = np.float32(matched_all) / total_all
                    if (thresh_match >= (Tbuffer * record_thresh)) and (base_h < (Max_cl_height - i_step)) and (record_thresh < 0.95):
                        if thresh_match > record_thresh:
                            record_thresh = thresh_match
                            record_h = h

                    elif record_thresh > Tsimilar:
                        similar_num[cld_label -1] = record_thresh # -1 to account for the zero based index used by Python (MATLAB is 1 one based).
                        i_vir = record_h / (sub_size * math.tan(sun_ele_rad))

                        if self.sunAzi < 180:
                            tmp_XY_type[1,:] = np.round(tmp_xys[1,:] - i_vir * math.cos(sun_tazi_rad)) # X is for col j,2
                            tmp_XY_type[0,:] = np.round(tmp_xys[0,:] - i_vir * math.sin(sun_tazi_rad)) # Y is for row i,1
                        else:
                            tmp_XY_type[1,:] = np.round(tmp_xys[1,:] + i_vir * math.cos(sun_tazi_rad)) # X is for col j,2
                            tmp_XY_type[0,:] = np.round(tmp_xys[0,:] + i_vir * math.sin(sun_tazi_rad)) # Y is for row i,1

                        tmp_scol = tmp_XY_type[1,:]
                        tmp_srow = tmp_XY_type[0,:]

                        # put data within range
                        tmp_srow[tmp_srow < 0] = 0
                        tmp_srow[tmp_srow >= win_height] = win_height - 1
                        tmp_scol[tmp_scol < 0] = 0
                        tmp_scol[tmp_scol >= win_width] = win_width - 1

                        tmp_sid = [tmp_srow, tmp_scol]
                        # give shadow_cal=1
                        shadow_cal[tmp_sid] = 1

                        break
                    else:
                        record_thresh = 0.0

            # # dilate each cloud and shadow object by 3 outward in 8 connect directions
            
            # The number of iterations is equal to the number of dilations if using a 3x3 structuring element.
            SEc  = cldpix
            SEc  = np.ones((SEc, SEc), 'uint8')
            SEs  = 2 * sdpix + 1
            SEs  = np.ones((SEs, SEs), 'uint8')
            SEsn =  snpix
            SEsn = np.ones((SEsn, SEsn), 'uint8')

            # dilate shadow first
            shadow_cal = scipy.ndimage.morphology.binary_dilation(shadow_cal, structure=SEs)

            segm_cloud_tmp = (segm_cloud != 0)
            cloud_cal = scipy.ndimage.morphology.binary_dilation(segm_cloud_tmp, structure=SEc)

            Snow = scipy.ndimage.morphology.binary_dilation(Snow, structure=SEsn)

        if self.mode == "Only Snow":
            Snow[boundary_test == 0] = 255
            return Snow

        elif self.mode == "Cloud + Shadow":
            cloud_cal[boundary_test == 0] = 255
            cloud_cal[shadow_cal == 1] = 1
            return cloud_cal
            
        else:
            cloud_cal[boundary_test == 0] = 255
            return cloud_cal

    # viewgeo - Calculate the geometric parameters needed for the cloud/shadow match
    def viewgeo(self, x_ul, y_ul, x_ur, y_ur, x_ll, y_ll, x_lr, y_lr):
        x_u = (x_ul + x_ur) / 2
        x_l = (x_ll + x_lr) / 2
        y_u = (y_ul + y_ur) / 2
        y_l = (y_ll + y_lr) / 2

        if (x_ul != x_ur): # get k of the upper left and right points
            K_ulr = (y_ul - y_ur) /  (x_ul - x_ur)
        else:
            K_ulr = 0.0

        if (x_ll != x_lr): # get k of the lower left and right points
            K_llr = (y_ll - y_lr) /  (x_ll - x_lr)
        else:
            K_llr = 0.0

        K_aver = (K_ulr + K_llr) / 2
        omiga_par = math.atan(K_aver) # get the angle of parallel lines k (in pi)

        A = y_u - y_l
        B = x_l - x_u
        C = y_l * x_u - x_l * y_u


        omiga_per = math.atan( B / A) # get the angle which is perpendicular to the trace line
        return (A,B,C,omiga_par,omiga_per)

    # mat_truecloud - Calculate shadow pixel locations of a true cloud segment
    def mat_truecloud(self, x, y, h, A, B, C, omiga_par, omiga_per):
        H = 705000                      # average Landsat height (m)
        dist = (A * x + B * y + C) / math.sqrt(A * A + B * B)
        dist_par = dist / math.cos(omiga_per - omiga_par)
        dist_move = dist_par * h / H    # cloud move distance (m)
        delt_x = dist_move * math.cos(omiga_par)
        delt_y = dist_move * math.sin(omiga_par)

        x_new = x + delt_x              # new x, j
        y_new = y + delt_y              # new y, i

        return (x_new, y_new)

    def imfill(self, band):
        seed = band.copy()

        # Borders masked with maximum value of image
        seed[1:-1, 1:-1] = band.max()

        # Define the mask; Probably unneeded.
        mask = band

        # Fill the holes - Equivalent of imfill
        filled = morphology.reconstruction(seed, mask, method='erosion')

        return filled
