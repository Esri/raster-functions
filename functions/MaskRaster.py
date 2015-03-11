import numpy as np


class MaskRaster():

    def __init__(self):
        self.name = "Mask Raster Function"
        self.description = "Applies a raster as the NoData mask of the input raster."

    def getParameterInfo(self):
        return [
            {
                'name': 'r',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster."
            },
            {
                'name': 'm',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Mask Raster",
                'description': "The input mask raster."
            },
        ]

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        pixelBlocks['output_pixels'] = pixelBlocks['r_pixels'].astype(props['pixelType'], copy=False)
        m = pixelBlocks['m_pixels'].astype('u1', copy=False) > 0
        pixelBlocks['output_mask'] = np.putmask(np.zeros(shape, 'u1'), m, 1)
        return pixelBlocks
