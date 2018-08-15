import numpy as np
from numpy import pi
#import datetime
import scipy.stats as stats
#from datetime import timedelta
#import sys


#import os
#import pickle

#debug_logs_directory = r'C:\PROJECTS\gbrunner-raster-functions\pickles'

# Based on QA Band - https://landsat.usgs.gov/collectionqualityband
#QA_BAND_NUM = 7
#misc = [0, 1]
LANDSAT_4_7_CLEAR_PIX_VALS = [672, 676, 680, 684]
LANDSAT_8_CLEAR_PIX_VALS = [20480, 20484, 20512, 23552]#[2720, 2724, 2728, 2732]
LANDSAT_CLEAR_PIX_VALS = LANDSAT_4_7_CLEAR_PIX_VALS + LANDSAT_8_CLEAR_PIX_VALS

# Terrain C-Correction based on the following papers:
# 1. Teillet, Guindon, and Goodenough (1982)
# 2. Sola et al (2016)
# 3. Holben et al (1980) https://www.asprs.org/wp-content/uploads/pers/1980journal/sep/1980_sep_1191-1200.pdf
# 4. Dr. Mort Canty - https://github.com/mortcanty/CRCPython

class TopographicCCorrection():

    def __init__(self):
        self.name = 'Topographic C Correction'
        self.description = 'Topographic C-Correction based on the paper from Teillet, Guindon, and Goodenough (1982).'

        self.metadata = []

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Rasters',
                'description': 'The collection of overlapping rasters to aggregate.'
            },
            {
                'name': 'slope',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Slope",
                'description': "Slope Derived from Digital Elevation Model."
            },
            {
                'name': 'aspect',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Aspect",
                'description': "Aspect Derived from Digital Elevation Model."
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,         # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,      # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': True,                  # need raster mask of all input rasters in .updatePixels().
            'resampling': False,                # process at native resolution
            'keyMetadata': ['SunAzimuth','SunElevation','AcquisitionDate']
        }

    def updateRasterInfo(self, **kwargs):
        #outStats = {'minimum': -1, 'maximum': 1}
        #self.outBandCount = 6

        kwargs['output_info']['pixelType'] = 'f4'           # output pixels are floating-point values
        kwargs['output_info']['histogram'] = ()             # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()            # outStatsTuple

        self.metadata = kwargs['rasters_keyMetadata']

        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata


    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        #fname = '{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        #filename = os.path.join(debug_logs_directory, fname)

        image_pix_blocks = pixelBlocks['rasters_pixels']
        image_pix_array = np.asarray(image_pix_blocks)
        ##pickle_filename = os.path.join(debug_logs_directory, fname)
        ##pickle.dump(image_pix_array, open(pickle_filename[:-4]+'landsat.p',"wb"))

        slope_pix_blocks = pixelBlocks['slope_pixels']
        slope_pix_array = np.asarray(slope_pix_blocks)
        slope_rads = slope_pix_array * pi/180
        ##pickle_filename = os.path.join(debug_logs_directory, fname)
        ##pickle.dump(slope_rads, open(pickle_filename[:-4]+'slope.p',"wb"))

        aspect_pix_blocks = pixelBlocks['aspect_pixels']
        aspect_pix_array = np.asarray(aspect_pix_blocks)
        aspect_rads = aspect_pix_array * pi/180
        ##pickle_filename = os.path.join(debug_logs_directory, fname)
        ##pickle.dump(aspect_rads, open(pickle_filename[:-4]+'aspect.p',"wb"))


        t_vals = [j['acquisitiondate'] for j in self.metadata]
        sun_az = [j['sunazimuth'] for j in self.metadata]
        sun_el = [j['sunelevation'] for j in self.metadata]

        #https://en.wikipedia.org/wiki/Solar_zenith_angle
        sun_ze = [(90 - el) for el in sun_el]


        #Equation
        #Corrected Image = Image * (cos(solar zenith angle) + C)/(cos(solar incidence angle) + C)
        #Where C is an empiraicle parameter
        #cos(solar incidence angle) =
        pix_array_dim = image_pix_array.shape
        num_bands = pix_array_dim[1]
        num_squares_x = pix_array_dim[2]
        num_squares_y = pix_array_dim[3]
        result = np.zeros((num_bands, num_squares_x, num_squares_y))

        if len(sun_az) == 1:
            sun_az_rad = sun_az[0] * pi / 180
            sun_ze_rad = sun_ze[0] * pi / 180

            # Topographic Effect on Spectral Response from Nadir-Pointing Sensors
            # https://www.asprs.org/wp-content/uploads/pers/1980journal/sep/1980_sep_1191-1200.pdf
            cos_i = (np.cos(slope_rads[0, :, :]) * np.cos(sun_ze_rad)) + \
                    (np.sin(slope_rads[0, :, :] * np.sin(sun_ze_rad)) * (np.cos(sun_az_rad - aspect_rads[0, :, :])))

            for k in range(num_bands):
                image_flattened = image_pix_array[0, k, :, :].ravel()
                cos_gamma = cos_i.ravel()

                # Adding linear regression from Dr. Mort Canty - https://github.com/mortcanty/CRCPython
                m, b, r, _, _ = stats.linregress(cos_gamma, image_flattened)

                C = b / m

                result[k, :, :] = image_pix_array[0, k, :, :] * (np.cos(sun_ze_rad) + C) / (cos_i + C)


        mask = np.ones((pix_array_dim[1], num_squares_x, num_squares_y))
        pixelBlocks['output_mask'] = mask.astype('u1', copy = False)
        pixelBlocks['output_pixels'] = result.astype(props['pixelType'], copy=False)

        return pixelBlocks
