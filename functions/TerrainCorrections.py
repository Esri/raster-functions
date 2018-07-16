import numpy as np
import datetime
from datetime import timedelta
import sys


import os
import pickle

debug_logs_directory = r'C:\PROJECTS\gbrunner-raster-functions\pickles'

# Based on QA Band - https://landsat.usgs.gov/collectionqualityband
#QA_BAND_NUM = 7
#misc = [0, 1]
LANDSAT_4_7_CLEAR_PIX_VALS = [672, 676, 680, 684]
LANDSAT_8_CLEAR_PIX_VALS = [20480, 20484, 20512, 23552]#[2720, 2724, 2728, 2732]
LANDSAT_CLEAR_PIX_VALS = LANDSAT_4_7_CLEAR_PIX_VALS + LANDSAT_8_CLEAR_PIX_VALS


class TerrainCorrections():

    def __init__(self):
        self.name = 'Terrain Corrections'
        self.description = 'TBD.'

        #self.metadata = []
        self.predict_month = None

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Rasters',
                'description': 'The collection of overlapping rasters to aggregate.'
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
        #kwargs['output_info']['bandCount'] = self.outBandCount   # number of output bands.

        self.metadata = kwargs['rasters_keyMetadata']

        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata


    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        fname = '{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        filename = os.path.join(debug_logs_directory, fname)

        file = open(filename,"w")
        file.write("File Open.\n")

        t_vals = [j['acquisitiondate'] for j in self.metadata]
        sun_az = [j['sunazimuth'] for j in self.metadata]
        sun_el = [j['sunelevation'] for j in self.metadata]


        pickle_filename = os.path.join(debug_logs_directory, fname)
        pickle.dump(t_vals, open(pickle_filename[:-4]+'pix_time.p',"wb"))

        file.write("Dump 1.\n")

        pickle_filename = os.path.join(debug_logs_directory, fname)
        pickle.dump(sun_el, open(pickle_filename[:-4]+'sun_el.p',"wb"))

        file.write("Dump 2.\n")

        pickle_filename = os.path.join(debug_logs_directory, fname)
        pickle.dump(sun_az, open(pickle_filename[:-4]+'sun_az.p',"wb"))
        #file.write(str(len(pix_time))+ "\n")

        file.write("Dump 3.\n")

        pix_blocks = pixelBlocks['rasters_pixels']
        pix_array = np.asarray(pix_blocks)

        file.close()



        #mask = np.ones((pix_array_dim[1], num_squares_x, num_squares_y))
        #pixelBlocks['output_mask'] = mask.astype('u1', copy = False)
        pixelBlocks['output_pixels'] = pix_array.astype(props['pixelType'], copy=False)

        return pixelBlocks
