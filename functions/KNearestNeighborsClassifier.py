import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


'''
This raster function performs k-nearest neighbors classification 
using scikit-learn and generates a map of the classification of 
each pixel.

http://scikit-learn.org/stable/documentation.html
http://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html#sklearn.neighbors.NearestNeighbors
https://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html#numpy.loadtxt
'''

class KNNClassifier():
    def __init__(self):
        self.name = 'K-Nearest Neighbor Classifier'
        self.description = 'This raster function performs k-nearest neighbors classification' \
                           ' using scikit-learn and generates a map of the classification of' \
                           ' each pixel.'

        # The number of neighbors to use
        self.n_neighbors = None

        # The CSV file containing the training data
        # The inputs is a string
        self.training_data_from_file = None

    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Input Rasters',
                'description': 'This should include several individual rasters. The rasters must be in the same order as the columns in the CSV file'
            },
            {
                'name': 'n_neighbors',
                'dataType': 'numeric',
                'value': 5,
                'required': True,
                'displayName': 'Number of neighbors (integer)',
                'description': 'Number of neighbors to use by default for kneighbors queries (integer).'
            },
            {
                'name': 'training_data_from_file',
                'dataType': 'string',
                'value': 'C:\\PROJECTS\\ML\\training_data.csv',
                'required': True,
                'displayName': 'Training data CSV filepath',
                'description': 'Full filepath directory to training data CSV. '
                               'Internally this will load from disk and be converted to a numpy array.'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8       # reset stats, histogram, key properties
        }

    def updateRasterInfo(self, **kwargs):
        self.n_neighbors = int(kwargs['n_neighbors'])
        self.datafile = str(kwargs['training_data_from_file'])

        # Number of output bands:
        # There should be one band for each neighbor calculated
        #out_band_count = self.n_neighbors

        # Output pixel information
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['bandCount'] = 1

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        # Read the input CSV file into a dataframe
        self.df = pd.read_csv(self.datafile)#(datafile)

        # Drop the fields that are not involved in predicting or mapping the values.
        # These fields will generally be things like "OBJECTID".
        fields_to_drop = ['OBJECTID', 'LOCATION_X', 'LOCATION_Y'] # Fields that aren't used in the analysis
        self.df.drop(fields_to_drop, axis=1, inplace=True)

        # Separate dataframe into training environmental variables and observed values.
        # The environmental values, x_train, are used to train the model
        # We are trying to map\predict the y_train value
        y_val =  'VarToPredict' # The value that you probably want to predict
        x_train = self.df.loc[:, self.df.columns != y_val]
        y_train = self.df[y_val]

        # The model won't work if there is missing or null data.
        # Fill null values with 0 (or some other value)
        x_train.fillna(0, inplace=True)
        y_train.fillna(0, inplace=True)

        # Read pixel blocks
        pix_blocks = pixelBlocks['rasters_pixels']

        # Convert pixel blocks to numpy array
        pix_array = np.asarray(pix_blocks)

        # Remove any extra indices
        pix_array = np.squeeze(pix_array)

        # Reshape the pixels into a 2D array that is number of pixels x number of predictor variables
        pixels_reshaped = pix_array.reshape(pix_array.shape[0], -1).transpose()

        # Classify each point using the k-neighbors classifier
        knn = KNeighborsClassifier(n_neighbors=self.n_neighbors)
        pred = knn.fit(x_train, y_train).predict(pixels_reshaped)

        # Reshape into a 2D array
        res = pred.reshape((pix_array.shape[1], pix_array.shape[2]))

        # Write output pixels
        pixelBlocks['output_pixels'] = res.astype(
            props['pixelType'],
            copy=True
        )

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata
