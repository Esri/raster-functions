import numpy as np

class Landsat8QA():

    def __init__(self):
        self.name = "Landsat 8 Collection 2 QA Mask"
        self.description = "This function creates masks based on Landsat 8 Collection 2 QA band."
        self.bit_index = {'fill': 0, 'diluted': 1, 'cirrus': 2, 'cloud': 3, 'shadow': 4, 'snow': 5, 'clear': 6, 'water': 7}

    def getParameterInfo(self):
        return [
            {
                'name': 'r',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Landsat 8 QA band",
                'description': "The input QA raster."
            },
            {
                'name': 'fill',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask fill data",
                'description': "Set fill data pixels to 1"
            },
            {
                'name': 'diluted',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask dilated cloud",
                'description': "Set dilated cloud pixels to 1"
            },
            {
                'name': 'cirrus',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask cirrus cloud",
                'description': "Set cirrus cloud pixels to 1"
            },
            {
                'name': 'cloud',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask cloud",
                'description': "Set cloud pixels to 1"
            },
            {
                'name': 'shadow',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask cloud shadow",
                'description': "Set cloud shadow pixels to 1"
            },
            {
                'name': 'snow',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask snow",
                'description': "Set snow pixels to 1"
            },
            {
                'name': 'clear',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask clear",
                'description': "Set clear pixels to 1"
            },
            {
                'name': 'water',
                'dataType': 'boolean',
                'value': False,
                'required': False,
                'displayName': "Mask water",
                'description': "Set water pixels to 1"
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 2 | 4 | 8,     # inherit all from the raster but raster type
            'invalidateProperties': 2 | 4 | 8,      # reset stats, histogram, key properties
            'inputMask': False
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['histogram'] = ()  # reset histogram
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 1.0}, )

        fill = kwargs.get('fill')
        diluted = kwargs.get('diluted')
        cirrus = kwargs.get('cirrus')
        cloud = kwargs.get('cloud')
        shadow = kwargs.get('shadow')
        snow = kwargs.get('snow')
        clear = kwargs.get('clear')
        water = kwargs.get('water')

        self.bit_mask = (fill << self.bit_index['fill']) + (diluted << self.bit_index['diluted']) + (cirrus << self.bit_index['cirrus']) + (cloud << self.bit_index['cloud']) + (shadow << self.bit_index['shadow']) + (snow << self.bit_index['snow']) + (clear << self.bit_index['clear']) + (water << self.bit_index['water'])

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        pix_blocks = pixelBlocks['r_pixels']
        pix_array = np.asarray(pix_blocks)
        z_dim, x_dim, y_dim = pix_array.shape

        out_mask = np.zeros(pix_array.shape)

        for num_x in range(x_dim):
            for num_y in range(y_dim):
                if pix_array[0, num_x, num_y] & self.bit_mask:
                    out_mask[0, num_x, num_y] = 1   # set pixels that have a flag set to 1, otherwise 0

        pixelBlocks['output_pixels'] = out_mask.astype(props['pixelType'], copy=False)

        return pixelBlocks
