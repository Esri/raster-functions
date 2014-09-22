import numpy as np


class SelectByPixelSize():

    def __init__(self):
        self.name = "Select by Pixel Size Function"
        self.description = ""
        self.threshold = 0.0

    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster A",
                'description': ""
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster B",
                'description': ""
            },
            {
                'name': 'threshold',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Cell Size Threshold",
                'description': ""
            },
        ]


    def getConfiguration(self, **scalars):
        self.threshold = scalars.get('threshold', 0.0)
        return { 'inputMask': True }


    def selectRasters(self, tlc, shape, props):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])
        if v < self.threshold:
            return ('r1',)
        else: return ('r2',)


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])

        raise Exception("{0}".format(v))

        if v < self.threshold:
            pixelBlocks['output_pixels'] = pixelBlocks['r1_pixels'].astype(props['pixelType'])
            pixelBlocks['output_mask'] = pixelBlocks['r1_mask'].astype('u1')
        else: 
            pixelBlocks['output_pixels'] = pixelBlocks['r2_pixels'].astype(props['pixelType'])
            pixelBlocks['output_mask'] = pixelBlocks['r2_mask'].astype('u1')

        return pixelBlocks

