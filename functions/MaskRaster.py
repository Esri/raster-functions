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

    def getConfiguration(self, **scalars):
        return { 
            'inputMask': True 
        }

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        M = np.zeros(shape, 'u1')
        I = (pixelBlocks['m_pixels'] > 0) & (pixelBlocks['m_mask'] > 0)
        np.putmask(M, I, 1)
        pixelBlocks['output_mask'] = M
        pixelBlocks['output_pixels'] = pixelBlocks['r_pixels'].astype(props['pixelType'], copy=False)
        return pixelBlocks
