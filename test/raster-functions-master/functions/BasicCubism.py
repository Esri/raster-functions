import numpy as np
import math

class BasicCubism():

    def __init__(self):
        self.name = "Basic Cubism"
        self.description = ("This python raster function sets the foundation for "
        "making cubism maps.  The takes a block of pixels, subdivides them into "
        "larger chunks, and colorizes them by their elevation.")

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
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['noData'] = np.array([0], 'f4')
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input DEM raster pixel block
        inBlock_dem = pixelBlocks['dem_pixels']

        z = inBlock_dem.shape
        x, y = z[1],z[2]
        cubism = np.zeros(z)

        #init_pixel_buffer = 10 change this
        pixel_buffer = 1
        square_size = 5
        maximum = np.max(inBlock_dem)
        minimum = np.min(inBlock_dem)
        spread = maximum-minimum
        break_size = spread/((square_size-1)-1)
        class_breaks = {}
        for i in range(1,int(square_size)-1):
            class_breaks[i] = minimum+i*break_size
        num_squares_x = math.floor(x/square_size)
        num_squares_y = math.floor(y/square_size)

        for num_x in xrange(0,int(num_squares_x)):
            for num_y in xrange(0,int(num_squares_y)):
            #chuck_close[num_x*square_size:(num_x+1)*square_size, num_y*square_size:(num_y+1)*square_size] = mean #dem[num_x*square_size, num_y*square_size]
                cubism[0,num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer] = np.mean(inBlock_dem[0,num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer])#dem[num_x*square_size, num_y*square_size]#-1*dem[num_x*square_size, num_y*square_size]+maximum

        # format output pixels
        outBlocks = cubism.astype(props['pixelType'], copy=False)
        pixelBlocks['output_pixels'] = outBlocks
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                                 # dataset level
            keyMetadata['datatype'] = 'Scientific'
        else:                                               # output "band"
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'CTI'
        return keyMetadata
