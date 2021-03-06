import numpy as np
import math

class HexagonPixels():

    def __init__(self):
        self.name = "Hexagon Pixels"
        self.description = ("Creates a DEM raster of hexagons.")

    def getParameterInfo(self):
        return [
            {
                'name': 'dem',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "DEM Raster",
                'description': "The digital elevation model (DEM)."
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit all from the raster
            'invalidateProperties': 2 | 4 | 8,      # reset stats, histogram, key properties
            'inputMask': False
        }

    def updateRasterInfo(self, **kwargs):
        # repeat stats for all output raster bands
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['histogram'] = ()  # reset histogram
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['noData'] = np.array([0], 'u1')

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input DEM raster pixel block
        inBlock_dem = pixelBlocks['dem_pixels']
        hex_pixels = np.zeros(inBlock_dem.shape)
        x, y = inBlock_dem.shape
        x_pix_size = 9 #8
        y_pix_size = 7
        maximum = np.max(inBlock_dem)
        minimum = np.min(inBlock_dem)
        spread = maximum-minimum
        num_squares_x = math.floor(x/x_pix_size)
        num_squares_y = math.floor(y/y_pix_size)

        #Loop 1 te generate first hexagons
        for num_x in range(1,int(num_squares_x)):
            for num_y in range(1,int(num_squares_y)):

                pix = np.mean(inBlock_dem[(num_x-1)*x_pix_size:(num_x-1)*x_pix_size+8, (num_y-1)*y_pix_size:(num_y-1)*y_pix_size+6])

                hex_pixels[(num_x-1)*x_pix_size+3:(num_x-1)*x_pix_size+6,(num_y-1)*y_pix_size+0] = pix
                hex_pixels[(num_x-1)*x_pix_size+2:(num_x-1)*x_pix_size+7,(num_y-1)*y_pix_size+1] = pix
                hex_pixels[(num_x-1)*x_pix_size+1:(num_x-1)*x_pix_size+8,(num_y-1)*y_pix_size+2] = pix
                hex_pixels[(num_x-1)*x_pix_size+0:(num_x-1)*x_pix_size+9,(num_y-1)*y_pix_size+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+1:(num_x-1)*x_pix_size+8,(num_y-1)*y_pix_size+4] = pix
                hex_pixels[(num_x-1)*x_pix_size+2:(num_x-1)*x_pix_size+7,(num_y-1)*y_pix_size+5] = pix
                hex_pixels[(num_x-1)*x_pix_size+3:(num_x-1)*x_pix_size+6,(num_y-1)*y_pix_size+6] = pix

        #Loop 2 to overlay the hexagons on top of the result of loop 1
        for num_x in range(1,int(num_squares_x)):
            for num_y in range(1,int(num_squares_y)):

                pix = np.mean(inBlock_dem[(num_x-1)*x_pix_size+4:(num_x-1)*x_pix_size+8+4, (num_y-1)*y_pix_size+3:(num_y-1)*y_pix_size+6+3])

                hex_pixels[(num_x-1)*x_pix_size+3+4:(num_x-1)*x_pix_size+6+4,(num_y-1)*y_pix_size+0+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+2+4:(num_x-1)*x_pix_size+7+4,(num_y-1)*y_pix_size+1+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+1+4:(num_x-1)*x_pix_size+8+4,(num_y-1)*y_pix_size+2+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+0+4:(num_x-1)*x_pix_size+9+4,(num_y-1)*y_pix_size+3+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+1+4:(num_x-1)*x_pix_size+8+4,(num_y-1)*y_pix_size+4+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+2+4:(num_x-1)*x_pix_size+7+4,(num_y-1)*y_pix_size+5+3] = pix
                hex_pixels[(num_x-1)*x_pix_size+3+4:(num_x-1)*x_pix_size+6+4,(num_y-1)*y_pix_size+6+3] = pix

        # format output pixels
        outBlocks = hex_pixels.astype(props['pixelType'], copy=False)
        pixelBlocks['output_pixels'] = outBlocks
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                                 # dataset level
            keyMetadata['datatype'] = 'Scientific'
        else:                                               # output "band"
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'GIS is Art'
        return keyMetadata



