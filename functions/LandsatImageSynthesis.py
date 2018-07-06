import numpy as np
import datetime
from datetime import timedelta
import sys


import os
import pickle

#debug_logs_directory = r'C:\PROJECTS\TEMP'

# Based on QA Band - https://landsat.usgs.gov/collectionqualityband
LANDSAT_4_7_CLEAR_PIX_VALS = [672, 676, 680, 684]
LANDSAT_8_CLEAR_PIX_VALS = [20480, 20484, 20512, 23552]#[2720, 2724, 2728, 2732]
LANDSAT_CLEAR_PIX_VALS = LANDSAT_4_7_CLEAR_PIX_VALS + LANDSAT_8_CLEAR_PIX_VALS


class LandsatImageSynthesis():

    def __init__(self):
        self.name = 'Landsat Scene Synthesis'
        self.description = 'This function takes as input a spatial and temporal '\
                           'mosaic dataset of Landsat images, selects images ' \
                           'for user defined month, filters out cloudy '\
                           'pixels from each image in the stack, then '\
                           'averages the values along a spatial element to '\
                           'create a synthetic Landsat image for the '\
                           'user defined month.'

        self.times = []
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
            },
            {
                'name': 'sensor',
                'dataType': 'string',
                'value': 'Landsat TM',
                'required': True,
                'domain': ('Landsat TM', 'Landsat ETM', 'Landsat OLI'),
                'displayName': 'Landsat sensor to use',
                'description': 'Landsat TM, ETM, or OLI'
            },
            {
                'name': 'predict_month',
                'dataType': 'string',
                'value': 'Jun',
                'required': True,
                'domain': ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'),
                'displayName': 'Month to Predict',
                'description': 'Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,         # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,      # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': True,                  # need raster mask of all input rasters in .updatePixels().
            'resampling': False,                # process at native resolution
            'keyMetadata': ['AcquisitionDate']
        }

    def updateRasterInfo(self, **kwargs):
        #outStats = {'minimum': -1, 'maximum': 1}
        #self.outBandCount = 6

        kwargs['output_info']['pixelType'] = 'f4'           # output pixels are floating-point values
        kwargs['output_info']['histogram'] = ()             # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()            # outStatsTuple
        #kwargs['output_info']['bandCount'] = self.outBandCount   # number of output bands.

        self.times = kwargs['rasters_keyMetadata']
        month_dict = {'Jan':1,
            'Feb':2,
            'Mar':3,
            'Apr':4,
            'May':5,
            'Jun':6,
            'Jul':7,
            'Aug':8,
            'Sep':9,
            'Oct':10,
            'Nov':11,
            'Dec':12}

        self.predict_month = int(month_dict[kwargs['predict_month']])

        self.sensor = kwargs['sensor']

        if self.sensor == 'Landsat TM' or self.sensor == 'Landsat ETM':
            self.filter = LANDSAT_4_7_CLEAR_PIX_VALS
            self.qa_band_num = 7
        elif self.sensor == 'Landsat OLI':
            self.filter = LANDSAT_8_CLEAR_PIX_VALS
            self.qa_band_num = 9
        else:
            self.filter = LANDSAT_CLEAR_PIX_VALS
            self.qa_band_num = 7

        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata


    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        #fname = '{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        #filename = os.path.join(debug_logs_directory, fname)

        #file = open(filename,"w")
        #file.write("File Open.\n")

        pix_time = [j['acquisitiondate'] for j in self.times]

        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_time, open(pickle_filename[:-4]+'pix_time.p',"wb"))

        #file.write(str(len(pix_time))+ "\n")

        pix_blocks = pixelBlocks['rasters_pixels']
        pix_array = np.asarray(pix_blocks)

        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_blocks, open(pickle_filename[:-4]+'pix_blocks.p',"wb"))

        pix_array_dim = pix_array.shape
        num_bands = pix_array_dim[1]-1
        num_squares_x = pix_array_dim[2]
        num_squares_y = pix_array_dim[3]

        d = datetime.datetime(1900, 1,1)

        datetime_list = []
        idx_list = []
        for idx,t in enumerate(pix_time):
            year = timedelta(days=t)
            date = year+d
            if date.month == self.predict_month:
                idx_list.append(idx)
                datetime_list.append(year+d)

        pix_array_within = pix_array[idx_list, :, :, :]
        #out_band_num = self.outBandCount
        output_pixels =  np.zeros((pix_array_dim[1], num_squares_x, num_squares_y))

        qa_band_ind = self.qa_band_num - 1
        for num_x in range(0, int(num_squares_x)):
            for num_y in range(0, int(num_squares_y)):

                clear_indices = [
                    x for x in range(len(pix_array_within[:, qa_band_ind, num_x, num_y]))
                    if pix_array_within[x, qa_band_ind, num_x, num_y]
                       in self.filter
                ]

                if len(clear_indices) > 0:
                    for num_b in range(0, int(num_bands)):
                        output_pixels[num_b, num_x, num_y] = np.mean(pix_array_within[clear_indices, num_b, num_x, num_y])

                else:
                    output_pixels[:, num_x, num_y] = -1

        mask = np.ones((pix_array_dim[1], num_squares_x, num_squares_y))
        pixelBlocks['output_mask'] = mask.astype('u1', copy = False)
        pixelBlocks['output_pixels'] = output_pixels.astype(props['pixelType'], copy=False)

        return pixelBlocks
