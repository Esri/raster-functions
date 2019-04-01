import numpy as np
from datetime import timedelta
import datetime
#import sys

#import os
#import pickle

#debug_logs_directory =

class PercentAboveThreshold():

    def __init__(self):
        self.name = 'Percent Above or Below Threshold'
        self.description = 'Calculates the percentage of pixels that are above or below' \
                           'a threshold value. The threshold value is set in the raster function.' \
                           'The raster function can be applied to a time-enabled stack of rasters in ' \
                           'a mosaic dataset.'

        self.times = []
        self.start_year = None
        self.end_year = None
        self.threshold = 50

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Rasters',
                'description': 'The collection of rasters to analyze.',
            },
            {
                'name': 'start_date',
                'dataType': 'string',
                'value': '1/1/2019 12:30:00',
                'required': True,
                'displayName': 'Start Date',
                'description': 'The beginning date of analysis (inclusive of entire year).',
            },
            {
                'name': 'end_date',
                'dataType': 'string',
                'value': '12/31/2019 23:30:00',
                'required': True,
                'displayName': 'End Date',
                'description': 'The final date of analysis (inclusive of entire year).',
            },
            {
                'name': 'threshold',
                'dataType': 'numeric',
                'value': 45,
                'required': True,
                'displayName': 'Value Threshold',
                'description': 'Value Threshold.',
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,  # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,  # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': True,  # need raster mask of all input rasters in .updatePixels().
            'resampling': False,  # process at native resolution
            'keyMetadata': ['AcquisitionDate']
        }

    def updateRasterInfo(self, **kwargs):
        # outStats = {'minimum': -1, 'maximum': 1}
        # outStatsTuple = tuple(outStats for i in range(outBandCount))

        kwargs['output_info']['pixelType'] = 'f4'  # output pixels are floating-point values
        kwargs['output_info']['histogram'] = ()  # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()  # outStatsTuple
        #kwargs['output_info'][
        #    'bandCount'] = outBandCount  # number of output bands. 7 time bands, 3 TC bands, creates 21 bands

        self.times = kwargs['rasters_keyMetadata']
        self.start_date = kwargs['start_date']
        self.end_date = kwargs['end_date']
        self.threshold = int(kwargs['threshold'])

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
        #pickle.dump(pix_array, open(pickle_filename[:-4]+'pix_blocks.p',"wb"))

        pix_array_dim = pix_array.shape
        num_squares_x = pix_array_dim[2]
        num_squares_y = pix_array_dim[3]

        #file.write("Filtering Based on Time\n")

        # This worked before I added time Filtering:
        #pix_as_array = np.reshape(pix_array, -1)
        #total_count = np.size(pix_as_array)
        #vals_above_thresh_count = np.size(np.where(pix_as_array <= self.threshold))
        #outBlock = np.ones((num_squares_x, num_squares_y)) * (vals_above_thresh_count / total_count) * 100

        t_array = []
        ind_array = []
        start_date = self.start_date #"1/1/2019 12:30:00"
        end_date = self.end_date #"7/7/2019 12:30:00"
        start_datetime = datetime.datetime.strptime(start_date, '%m/%d/%Y %H:%M:%S')  # %p')
        end_datetime = datetime.datetime.strptime(end_date, '%m/%d/%Y %H:%M:%S')  # %p')
        for ind, time in enumerate(pix_time):
            temp_t = datetime.datetime(1900, 1, 1) + timedelta(time - 2)
            if temp_t >= start_datetime and temp_t <= end_datetime:
                t_array.append(temp_t)
                ind_array.append(ind)

        #time_within = [pix_time[x] for x in ind_array]
        pix_array_within = pix_array[ind_array, :, :, :]

        #threshold = 50
        pix_as_array = np.reshape(pix_array_within, -1)
        total_count = np.size(pix_as_array)
        vals_above_thresh_count = np.size(np.where(pix_as_array <= self.threshold)) #< below, > above
        outBlock = np.ones((num_squares_x, num_squares_y)) * (vals_above_thresh_count / total_count) * 100

        #file.write("DONE\n")
        #file.close()
        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'], copy=False)
        #masks = np.array(pixelBlocks['rasters_mask'], copy=False)
        #pixelBlocks['output_mask'] = np.all(masks, axis=0).astype('u1', copy=False)
        return pixelBlocks
