import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np

'''
A random forest classifier.

A random forest is a meta estimator that fits a number of decision tree classifiers on 
various sub-samples of the dataset and uses averaging to improve the 
predictive accuracy and control over-fitting. 
The sub-sample size is controlled with the max_samples parameter if bootstrap=True (default), 
otherwise the whole dataset is used to build each tree.

https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html?
highlight=random%20forest#sklearn.ensemble.RandomForestClassifier
'''

# Note: Can not name the class RandomForestClassifier because it will conflict
# with the scikit-learn class that is imported.
class RandomForest():
    def __init__(self):
        self.name = 'Random Forest Classifier'
        self.description = 'Random Forest Classifier implemented as a Python Raster Function'

        # inputs as string, but eventually will be numpy arrays
        self.df = None
        self.datafile = None
        self.threshold = 0.5


    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Input Rasters',
                'description': 'Must be in the same order as the columns in the CSV file'
            },
            {
                'name': 'training_data_from_file',
                'dataType': 'string',
                'value': 'C:\\PROJECTS\\ML\\training_data.csv',
                'required': True,
                'displayName': 'Training data CSV filepath',
                'description': 'Full filepath directory to training data CSV. '
                               'Internally this will load from disk and be converted to a pandas dataframe.'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8       # reset stats, histogram, key properties
        }

    def updateRasterInfo(self, **kwargs):

        # convert filepath string input param to numpy array
        self.datafile = str(kwargs['training_data_from_file'])
        #self.threshold = float(kwargs['threshold'])

        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['bandCount'] = 3

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        self.df = pd.read_csv(self.datafile)

        try:
            fields_to_drop = ['OBJECTID', 'LOCATION_X', 'LOCATION_Y']
            self.df.drop(fields_to_drop, axis=1, inplace=True)
        except:
            pass

        y_val = 'VarToPredict'  # The value that you probably want to predict
        x_train = self.df.loc[:, self.df.columns != y_val]
        y_train = self.df[y_val]
        x_train.fillna(0, inplace=True)
        y_train.fillna(0, inplace=True)

        # Initialize RandomForestClassifier
        # Recommend trying different values for:
        #  - n_estimators
        #  - max_features
        #  - random_state
        regr1 = RandomForestClassifier(n_estimators=20, random_state=0)  # max_features=13, random_state=1)
        regr1.fit(x_train, y_train)

        pix_blocks = pixelBlocks['rasters_pixels']
        pix_array = np.asarray(pix_blocks)
        pix_array = np.squeeze(pix_array)

        pixels_reshaped = pix_array.reshape(pix_array.shape[0], -1).transpose()

        # Run RandomForestRegressor
        pred = regr1.predict(pixels_reshaped)
        pred_proba = regr1.predict_proba(pixels_reshaped)

        res = np.hstack([np.expand_dims(pred, 1), pred_proba])

        #res = pred.reshape((pix_array.shape[1], pix_array.shape[2]))
        res_reshape = np.reshape(
            res.transpose(),
            (3, pix_array.shape[1], pix_array.shape[2])
        )

        res_reshape[res_reshape <= self.threshold] = 0

        pixelBlocks['output_pixels'] = res_reshape.astype(
            props['pixelType'],
            copy=True
        )

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata
