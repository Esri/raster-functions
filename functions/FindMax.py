import numpy as np
import datetime

# For Debugging
import os
import sys
#import pickle

#debug_logs_directory = r'C:\Users\greg6750\PycharmProjects\ArtPRF'

'''
This raster function performs nearest neighbors analysis using scikit-learn and then maps the
input values to the resulting neighbor array.

http://scikit-learn.org/stable/documentation.html
http://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html#sklearn.neighbors.NearestNeighbors
https://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html#numpy.loadtxt
'''

class FindMax():
    def __init__(self):
        self.name = 'FindIndex'
        self.description = 'Finds the index of the best raster.'



    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Input Rasters',
                'description': 'Rasters for analysis.'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            #'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,       # reset stats, histogram, key properties
            'resamplingType': 0
        }

    def updateRasterInfo(self, **kwargs):


        # Output pixel information
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['noData'] = 0
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['bandCount'] = 1
        # repeat stats for all output raster bands
        kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 25.0}, )


        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        fname = '{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        #filename = os.path.join(debug_logs_directory, fname)

        # Read pixel blocks
        pix_blocks = pixelBlocks['rasters_pixels']

        # Convert pixel blocks to numpy array
        pix_array = np.asarray(pix_blocks)
        array3d = np.squeeze(pix_array)
        array3d[array3d > 100] = -1
        #max_val = np.max(array3d, 0)
        maxind = np.max(array3d, axis=0)
        allzeros = np.max(array3d != -1, 0)
        maxind[allzeros == False] = -1

        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_blocks, open(pickle_filename[:-4]+'pix_blocks.p',"wb"))

        # Write output pixels
        pixelBlocks['output_pixels'] = maxind.astype(
            props['pixelType'],
            copy=False
        )

        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata