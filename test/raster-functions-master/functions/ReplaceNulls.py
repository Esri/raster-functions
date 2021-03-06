import numpy as np

class ReplaceNulls():
    def __init__(self):
        self.name = 'Replace Nulls'
        self.description = 'Replace NULL values in a raster with a user defined value.'



    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value':'Multiband Raster',
                'required': True,
                'displayName': 'Input Raster',
                'description': 'Input Raster'
            },
            {
                'name': 'fill_val',
                'dataType': 'numeric',
                'value': 1,
                'required': True,
                'displayName': 'Replace Value',
                'description': 'Value to replace with'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 1 | 2 | 4 | 8,         # inherit everything but the pixel type (1) and NoData (2)
            #'invalidateProperties': 1 | 2 | 4 | 8,      # invalidate histogram and statistics because we are modifying pixel values
            'resampling': False
        }

    def updateRasterInfo(self, **kwargs):
        
        self.fill_val = float(kwargs['fill_val'])
        # repeat stats for all output raster bands
        #kwargs['output_info']['statistics'] = tuple(outStats for i in range(self.out_band_count))
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ()

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):

        pix_array = np.asarray(pixelBlocks['raster_pixels'])
        np.place(pix_array, pix_array==0, [self.fill_val])

        mask      = np.ones(pix_array.shape)
        pixelBlocks['output_mask'] = mask.astype('u1', copy = False)
        pixelBlocks['output_pixels'] = pix_array.astype(props['pixelType'], copy=True)


        return pixelBlocks


    