import numpy as np
import statsmodels.api as sm
import pandas as pd
import datetime

# For Debugging
import os
import sys
import pickle

debug_logs_directory = r'C:\PROJECTS\gbrunner-raster-functions\pickles\daymet'

class SeasonalARIMA():

    def __init__(self):
        self.name = "Seasonal ARIMA"
        self.description = "This function performs a Seasonal AutoRegressive Integrated Moving Average (ARIMA) on " \
                           "a time-series of rasters. The function takes in the rasters as a mosaic dataset, trains " \
                           "a seasonal ARIMA model on the input mosaic dataset, and predicts the change in the " \
                           "observed variable (pixel values). This currently only supports single band time-series " \
                           "rasters that generally contain scientific data."
        self.times = []
        self.data_start_year = None
        self.predict_month = None
        self.predict_year = None
        self.train_start_year = None
        self.train_end_year = None
        self.p = None
        self.d = None
        self.q = None
        self.s = None

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': "Rasters",
                'description': "The collection of temporal reasters for which we want to predict seasonal change.",
            },
            {
                'name': 'data_start_year',
                'dataType': 'numeric',
                'value': 1980,
                'required': True,
                'displayName': 'Data Start Year',
                'description': 'The first year in the dataset'
            },
            {
                'name': 'train_start_year',
                'dataType': 'numeric',
                'value': 1980,
                'required': True,
                'displayName': 'Training Start Year',
                'description': 'The year on which to start training model'
            },
            {
                'name': 'train_end_year',
                'dataType': 'numeric',
                'value': 2010,
                'required': True,
                'displayName': 'Training End Year',
                'description': 'The year on which to end training model'
            },
            {
                'name': 'predict_year',
                'dataType': 'numeric',
                'value': 2050,
                'required': True,
                'displayName': 'Prediction Year',
                'description': 'The year for which we want to predict our seasonal variable'
            },
            {
                'name': 'predict_month',
                'dataType': 'string',
                'value': 'Jun',
                'required': True,
                'domain': ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'),
                'displayName': 'Month to Predict',
                'description': 'The month for which we want to predict the change in the observed variable.'
            },
            {
                'name': 'seasonal_order',
                'dataType': 'string',
                'value': '0,1,1,12',
                'required': True,
                'displayName': 'Seasonal Order (P, D, Q, s)',
                'description': 'The (P,D,Q,s) order of the seasonal component of the model for the AR parameters, ' \
                               'differences, MA parameters, and periodicity. d must be an integer indicating the ' \
                               'integration order of the process, while p and q may either be an integers indicating ' \
                               'the AR and MA orders (so that all lags up to those orders are included) or else ' \
                               'iterables giving specific AR and / or MA lags to include. s is an integer giving ' \
                               'the periodicity (number of periods in season), often it is 4 for quarterly data ' \
                               'or 12 for monthly data. Default is no seasonal effect.'
            }

        ]

    def getConfiguration(self, **scalars):

        return {
            'compositeRasters': False,
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,      # reset stats, histogram, key properties
            'inputMask': False,
            'keyMetadata': ['time'] #['StdTime']#
        }

    def updateRasterInfo(self, **kwargs):
        #outStats = {'minimum': 0,'maximum': 25}
        outBandCount = 1
        kwargs['output_info']['pixelType'] = 'f4'   # output pixels are floating-point values
        kwargs['output_info']['histogram'] = ()     # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['bandCount'] = outBandCount      # number of output bands.

        month_dict = {'Jan': 1,
                      'Feb': 2,
                      'Mar': 3,
                      'Apr': 4,
                      'May': 5,
                      'Jun': 6,
                      'Jul': 7,
                      'Aug': 8,
                      'Sep': 9,
                      'Oct': 10,
                      'Nov': 11,
                      'Dec': 12}

        self.data_start_year = int(kwargs['data_start_year'])
        self.predict_month = int(month_dict[kwargs['predict_month']])
        self.predict_year = int(kwargs['predict_year'])
        self.train_start_year = int(kwargs['train_start_year'])
        self.train_end_year = int(kwargs['train_end_year'])

        seasonal_order = kwargs['seasonal_order'].split(',')
        self.p = int(seasonal_order[0])
        self.d = int(seasonal_order[1])
        self.q = int(seasonal_order[2])
        self.s = int(seasonal_order[3])

        self.times = kwargs['rasters_keyMetadata']

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # pixelBlocks['rasters_pixels']: tuple of 3-d array containing pixel blocks from each input raster
        # apply the selected operator over each array in the tuple

        #fname = '{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        #filename = os.path.join(debug_logs_directory, fname)

        #file = open(filename,"w")
        #file.write("File Open.\n")

        pix_blocks = pixelBlocks['rasters_pixels']
        pix_array = np.asarray(pix_blocks)
        pix_time = [j['time'] for j in self.times]

        sorted_t = np.sort(pix_time)
        sorted_t_idx = np.argsort(pix_time)

        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_blocks, open(pickle_filename[:-4]+'pix_blocks.p',"wb"))

        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_time, open(pickle_filename[:-4]+'pix_time.p',"wb"))

        pix_array_dim = pix_array.shape
        num_squares_x = pix_array_dim[2]
        num_squares_y = pix_array_dim[3]
        new_stack = np.zeros((1, num_squares_x, num_squares_y))

        my_order = (1,0,0)
        my_seasonal_order = (self.p, self.d, self.q, self.s)

        now = datetime.datetime.now()
        current_year = int(now.year)
        data_start_year = self.data_start_year
        train_start_year = self.train_start_year
        predict_year = self.predict_year
        train_end_year = self.train_end_year
        predict_month = self.predict_month

        train_data_end_index = (train_end_year - data_start_year) * 12
        train_data_start_index = (train_start_year - data_start_year) * 12
        predict_data_end_index = (predict_year - train_end_year) * 12
        current_year_index = (current_year - train_end_year) * 12

        for num_x in range(0, int(num_squares_x)):
            for num_y in range(0, int(num_squares_y)):

                data = pix_array[:, 0, num_x, num_y]
                sorted_data = data[sorted_t_idx]
                try:
                    # define model
                    model = sm.tsa.statespace.SARIMAX(sorted_data[train_data_start_index:train_data_end_index],
                                                      order=my_order,
                                                      seasonal_order=my_seasonal_order, trend='c',
                                                      enforce_invertibility=False, enforce_stationarity=False)

                    model_fit = model.fit()
                    #index = (predict_year - train_end_year) * 12 + predict_month
                    yhat = model_fit.predict(start=train_data_end_index,
                                             end=train_data_end_index + predict_data_end_index)
                    final_year_prediction = yhat[predict_data_end_index - (12 - predict_month)]
                    current_year_prediction = yhat[current_year_index - (12 - predict_month)]
                    delta = final_year_prediction - current_year_prediction
                    new_stack[0, num_x, num_y] = delta
                    #print(delta, num_x, num_y)
                except:
                    delta = -999
                    new_stack[0, num_x, num_y] = delta
                    #print(delta, num_x, num_y)

        pixelBlocks['output_pixels'] = new_stack.astype(props['pixelType'], copy=False)#new_stack.astype(props['pixelType'], copy=False)

        #file.write("Done.")
        #file.close()

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata
