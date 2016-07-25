import numpy as np


class FillRaster():

    def __init__(self):
        self.name = "Fill Raster Function"
        self.description = ("")
        self.fillValue = 0.

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ""
            },
            {
                'name': 'value',
                'dataType': 'numeric',
                'value': 0,
                'required': True,
                'displayName': "Fill Value",
                'description': ("")
            },
        ]

    def updateRasterInfo(self, **kwargs):
        b = kwargs['raster_info']['bandCount']
        self.fillValue = kwargs.get('value', 0.)
        kwargs['output_info']['statistics'] = b * ({'minimum': self.fillValue, 'maximum': self.fillValue}, )
        kwargs['output_info']['histogram'] = ()
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        pixelBlocks['output_pixels'] = np.full(shape, self.fillValue, dtype=props['pixelType'])
        return pixelBlocks
