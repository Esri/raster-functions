import numpy as np
from numpy import pi
from math import sqrt

class CompoundTopographicIndex():

    def __init__(self):
        self.name = "Compound Topographic Index"
        self.description = ("Computes the compound topographic index (CTI), also "
                            "known as the topographic wetness index (TWI).  "
                            "This is calculated from an input slope raster and flow "
                            "accumulation surface and is meant to be used in "
                            "a raster function chain.")

    def getParameterInfo(self):
        return [
            {
                'name': 'slope',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Slope Raster",
                'description': "A slope raster (in degrees) derived from a digital elevation model (DEM)."
            },
            {
                'name': 'flow',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Flow Accumulation Raster",
                'description': "A raster representing flow accumulation."
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
        kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 25.0}, )
        kwargs['output_info']['histogram'] = ()  # reset histogram
        kwargs['output_info']['pixelType'] = 'f4'
        self.dem_cellsize = kwargs['slope_info']['cellSize']
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input DEM raster pixel block
        inBlock_slope = pixelBlocks['slope_pixels']
        inBlock_flow = pixelBlocks['flow_pixels']
        cellSize = self.dem_cellsize

        DX = cellSize[0]
        DY = cellSize[1]
        slope = calc_slope(inBlock_slope)
        cti = calc_cti(slope, inBlock_flow, cellSize[0])

        # format output cti pixels
        outBlocks = cti.astype(props['pixelType'], copy=False)
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

# supporting business logic functions
def calc_slope(slope_deg):
    slope = slope_deg * pi/180 #np.arctan(slope_deg)
    return slope

def calc_cti(slope, flow_acc, cellsize):
    tan_slope = np.tan(slope)
    tan_slope[tan_slope==0]=0.0001
    cti = np.log(((flow_acc+1)*cellsize)/tan_slope)
    return cti
