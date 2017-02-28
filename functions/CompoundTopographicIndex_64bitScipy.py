import numpy as np
from math import sqrt
from scipy import sparse as sp
from scipy.sparse import linalg as splg

class CompoundTopographicIndex_64bitScipy():

    def __init__(self):
        self.name = "Compound Topographic Index"
        self.description = ("Computes the compound topographic index (CTI), also "
                            "known as the topographic wetness index (TWI).")

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
        kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 25.0}, )
        kwargs['output_info']['histogram'] = ()  # reset histogram
        kwargs['output_info']['pixelType'] = 'f4'
        self.dem_cellsize = kwargs['dem_info']['cellSize']
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # get the input DEM raster pixel block
        inBlock_dem = pixelBlocks['dem_pixels']
        cellSize = self.dem_cellsize

        slope = calc_slope(inBlock_dem, cellSize[0])
        DX = cellSize[0]
        DY = cellSize[1]
        flow_direction = calc_flow_direction_d8(DX, DY, inBlock_dem)
        flow_accumulation = calc_flow_accumulation(flow_direction, inBlock_dem.shape)
        cti = calc_cti(slope, flow_accumulation, cellSize[0])

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
def calc_slope(dem, cellsize):
    #Modified from calculation found here:
    #http://geoexamples.blogspot.com/2014/03/shaded-relief-images-using-gdal-python.html

    x, y = np.gradient(dem, cellsize, cellsize)
    #slope = np.pi/2.0 - np.arctan(np.sqrt(x*x + y*y))
    slope = np.arctan(np.sqrt(x*x + y*y))
    return slope


def calc_flow_direction_d8(DX, DY, dem):
    #Backgroud found at http://adh.usace.army.mil/new_webpage/main/main_page.htm
    #Algorithm modified from http://adh.usace.army.mil/svn/adh/mfarthin/src/samsi/2013/topo/

    nr = dem.shape[0]
    nc = dem.shape[1]
    HYP = sqrt(DX*DX + DY*DY)

    ghost = np.zeros((nr+2, nc+2), 'd')
    ghost[1:-1, 1:-1] = dem[:, :]
    ghost[0, 1:-1] = dem[0, :]
    ghost[-1, 1:-1] = dem[-1, :]
    ghost[1:-1, 0] = dem[:, 0]
    ghost[1:-1, -1] = dem[:, -1]

    ghost[0, 0] = ghost[1, 1]
    ghost[-1, -1] = ghost[-2, -2]

    ghost[0, -1] = ghost[1, -2]
    ghost[-1, 0] = ghost[-2, 1]

    neig_incr_col_major = np.array([nr,
                                    nr-1, -1, -nr-1,
                                    -nr,
                                    -nr+1, 1, nr+1])

    neig_incr = neig_incr_col_major
    slopes = np.zeros((8,), 'd')
    all_indices = np.arange(nr*nc, dtype='i')
    max_indices = np.zeros(nr*nc, 'i')
    slope_vals = np.zeros(nr*nc, 'd')
    slope_count = np.zeros(nr*nc, 'i')
    for i in range(1, nr+1):
        for j in range(1, nc+1):
            #
            slopes[0] = (ghost[i, j]-ghost[i, j+1])/DX
            slopes[4] = (ghost[i, j]-ghost[i, j-1])/DX
            #
            slopes[1] = (ghost[i, j]-ghost[i-1, j+1])/HYP
            slopes[2] = (ghost[i, j]-ghost[i-1, j])/DY
            slopes[3] = (ghost[i, j]-ghost[i-1, j-1])/HYP
            #
            slopes[5] = (ghost[i, j]-ghost[i+1, j-1])/HYP
            slopes[6] = (ghost[i, j]-ghost[i+1, j])/DY
            slopes[7] = (ghost[i, j]-ghost[i+1, j+1])/HYP

            glob_ind = (j-1)*nr + i-1  # local cell col major
            loc_max = slopes.argmax()
            if slopes[loc_max] > 0:
                glob_max = min(max(glob_ind + neig_incr[loc_max], 0), nc*nr-1)
                max_indices[glob_ind] = glob_max
                slope_vals[glob_ind] = slopes[loc_max]
                slope_count[glob_ind] = 1

    M = sp.csr_matrix((slope_count, (all_indices, max_indices)), shape=(nr*nc, nr*nc))
    return M


def calc_flow_accumulation(M, dsh):
    #Backgroud found at http://adh.usace.army.mil/new_webpage/main/main_page.htm
    #Algorithm modified from http://adh.usace.army.mil/svn/adh/mfarthin/src/samsi/2013/topo/

    nc = M.shape[1]
    I = sp.eye(M.shape[0], M.shape[1])
    B = I - M.transpose()
    b = np.ones(nc, 'd')
    #a = sp.linalg.spsolve.spsolve(B, b)
    a = splg.spsolve(B, b)
    a = a.reshape(dsh, order='F')
    return a


def calc_cti(slope, flow_acc, cellsize):
    #Based on background infotmation found at
    #http://gis4geomorphology.com/topographic-index-model/
    #and
    #http://gis.stackexchange.com/questions/43276/can-compound-topographic-index-cti-topographic-wetness-index-twi-produce-n
    #and
    #https://wikispaces.psu.edu/display/AnthSpace/Compound+Topographic+Index

    tan_slope = np.tan(slope)
    tan_slope[tan_slope==0]=0.0001
    cti = np.log(((flow_acc+1)*cellsize)/tan_slope)
    return cti
