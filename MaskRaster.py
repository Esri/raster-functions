import numpy as np


class MaskRaster():

    def __init__(self):
        self.name = "Mask Raster Function"
        self.description = "Apply a raster as the NoData mask of an input raster."
        self.value = 1

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster."
            },
            {
                'name': 'mask',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Mask Raster",
                'description': "The input mask raster."
            },
        ]


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        pixelBlocks['output_pixels'] = pixelBlocks['raster_pixels']
        m = pixelBlocks['mask_pixels'].astype('u1') > 0

        outMask = np.zeros(shape, 'u1')
        np.putmask(outMask, m, 1)

        pixelBlocks['output_mask'] = outMask
        return pixelBlocks

