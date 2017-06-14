import numpy as np
import math

class BasicChuckClose():

    def __init__(self):
        self.name = "Basic Chuck Close"
        self.description = ("This python raster function is the first of which I "
            "plan to create that will transform imagery into artwork reminiscent of "
            "Chuck Close.")

    def getParameterInfo(self):
        return [
            {
                'name': 'dem',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "DEM Raster",
                'description': "The digital elevation model (DEM)."
            },
            {
                'name': 'inv',
                'dataType': 'boolean',
                'value': True,
                'required': True,
                'displayName': "Invert?",
                'description': "Inverts the image so that higher elevations are darker."
            },
            {
                'name': 'show_pix',
                'dataType': 'boolean',
                'value': False,
                'required': True,
                'displayName': "Colorize Pixels?",
                'description': "Gives pixels colors corresponding to their elevation."
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
        self.invert = kwargs.get('inv')
        self.show_pix = kwargs.get('show_pix')
        if not self.show_pix:
            kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 1.0}, )
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        #file = open(r'C:\PROJECTS\raster-functions\test.txt','w')
        #file.write(str(z))
        # get the input DEM raster pixel block
        inBlock_dem = pixelBlocks['dem_pixels']
        z = inBlock_dem.shape
        x, y = z[1],z[2]
        chuck_close = np.zeros(z)
        square_size = 13.0
        pixel_buffer = 7
        maximum = np.max(inBlock_dem)
        minimum = np.min(inBlock_dem)
        spread = maximum-minimum
        break_size = spread/((pixel_buffer-1))
        class_breaks = {}
        for i in range(0,int(pixel_buffer)):
            class_breaks[i] = minimum+i*break_size
        num_squares_x = math.floor(x/square_size)
        num_squares_y = math.floor(y/square_size)

        for num_x in range(1,int(num_squares_x)):
            for num_y in range(1,int(num_squares_y)):

                pix = np.mean(inBlock_dem[0,num_x*square_size:(num_x+1)*square_size, num_y*square_size:(num_y+1)*square_size])
                pixel_buffer = get_size(pix, class_breaks)

##                chuck_close[num_x*square_size-pixel_buffer:num_x*square_size+pixel_buffer, num_y*square_size-pixel_buffer:num_y*square_size+pixel_buffer] = 1 #np.mean(dem[num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer])#dem[num_x*square_size, num_y*square_size]#-1*dem[num_x*square_size, num_y*square_size]+maximum
                if self.invert:
                    if self.show_pix:
                        chuck_close[0,num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer]= pix #1 #np.mean(dem[num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer])#dem[num_x*square_size, num_y*square_size]#-1*dem[num_x*square_size, num_y*square_size]+maximum
                    else:
                        chuck_close[0,num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer]= 1

                else:
                    if self.show_pix:
                        chuck_close[0,num_x*square_size-pixel_buffer:num_x*square_size+pixel_buffer, num_y*square_size-pixel_buffer:num_y*square_size+pixel_buffer] = pix #1 #np.mean(dem[num_x*square_size+pixel_buffer:(num_x+1)*square_size-pixel_buffer, num_y*square_size+pixel_buffer:(num_y+1)*square_size-pixel_buffer])#dem[num_x*square_size, num_y*square_size]#-1*dem[num_x*square_size, num_y*square_size]+maximum
                    else:
                        chuck_close[0,num_x*square_size-pixel_buffer:num_x*square_size+pixel_buffer, num_y*square_size-pixel_buffer:num_y*square_size+pixel_buffer] = 1

        # format output cti pixels
        outBlocks = chuck_close.astype(props['pixelType'], copy=False)
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


def get_size(pixel_val, d):

    diff = float('inf')
    for key,value in d.items():
        if diff > abs(pixel_val-value):
            diff = abs(pixel_val-value)
            x = key

    if diff==float('inf'):
        x = 1

    return x
