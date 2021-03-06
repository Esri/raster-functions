import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
import numpy as np

'''
Gradient Boosting for classification.

GB builds an additive model in a forward stage-wise fashion; 
it allows for the optimization of arbitrary differentiable loss functions. 
In each stage n_classes_ regression trees are fit on the negative gradient of the binomial or 
multinomial deviance loss function. 
Binary classification is a special case where only a single regression tree is induced.

https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingClassifier.html?
highlight=gradient#sklearn.ensemble.GradientBoostingClassifier
'''

# Note: Can not name the class GradientBoostedClassifier because it will conflict
# with the scikit-learn class that is imported.
class BoostedClassifier():
    def __init__(self):
        self.name = 'Gradient Boosting Classifier (Boosted Regression Trees)'
        self.description = 'Gradient Boosting Classifier from scikit-learn ' \
                           'implemented as a Python Raster Function'

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

        y_val = 'VarToPredict'
        x_train = self.df.loc[:, self.df.columns != y_val]
        y_train = self.df[y_val]
        x_train.fillna(0, inplace=True)
        y_train.fillna(0, inplace=True)

        # Initialize RandomForestClassifier
        # Recommend trying different values for:
        #  - n_estimators
        #  - learning_rate
        #  - max_depth
        #  - random_state
        regr1 = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0,
                                        max_depth=3, random_state=0)
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

        res_reshape[res_reshape <= self.threshold] = 0.0

        #res[res <= self.threshold] = 0
        # remember that self.n_neighbors is the desired out band count
        #res = np.zeros(
        #    (pix_array.shape[1], pix_array.shape[2])
        #)

        pixelBlocks['output_pixels'] = res_reshape.astype(
            props['pixelType'],
            copy=True
        )

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata
