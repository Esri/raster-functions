import numpy as np


class Mask():

    def __init__(self):
        self.name = "Mask Function"
        self.description = "Apply a raster as a NoData mask"


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster",
                'description': "The primary input raster."
            },
            {
                'name': 'mask',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Mask",
                'description': "The input mask raster"
            },
        ]


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        pixelBlocks['output_pixels'] = pixelBlocks['raster_pixels']
        pixelBlocks['output_mask'] = pixelBlocks['mask_pixels'].astype('u1')
        return pixelBlocks

