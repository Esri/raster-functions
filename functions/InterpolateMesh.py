import arcpy
import numpy as np
from scipy import ndimage
from scipy import interpolate
import utils

class InterpolateMesh():

    def __init__(self):
        self.name = "Interpolate Mesh Function"
        self.description = ""
        self.interpolant = None
        self.trace = utils.getTraceFunction()

        
    def getParameterInfo(self):
        return [
            {
                'name': 'f',
                'dataType': 'string',
                'value': r"c:\Users\fero4752\Box Sync\Swap\mesh\temp.tif",
                'required': True,
                'displayName': "Value File",
                'description': "Path to the image file containing pixel values at each grid point.",
            },
            {
                'name': 'x',
                'dataType': 'string',
                'value': r"c:\Users\fero4752\Box Sync\Swap\mesh\lon_rho.tif",
                'required': True,
                'displayName': "X-Coordinates File",
                'description': "First dimension of the XY meshgrid.",
            },
            {
                'name': 'y',
                'dataType': 'string',
                'value': r"c:\Users\fero4752\Box Sync\Swap\mesh\lat_rho.tif",
                'required': True,
                'displayName': "Y-Coordinates File",
                'description': "",
            },
            {
                'name': 'sr',
                'dataType': 'numeric',
                'value': 4326,
                'required': False,
                'displayName': "Coordinate System (EPSG)",
                'description': "",
            },
        ]


    def updateRasterInfo(self, **kwargs):
        X = arcpy.RasterToNumPyArray(kwargs['x'])[0,:]
        Y = arcpy.RasterToNumPyArray(kwargs['y'])[:,0]
        F = arcpy.RasterToNumPyArray(kwargs['f'])
        self.trace("Trace|InterpolateMesh.updateRasterInfo.2|X: {0}|Y: {0}|F: {0}|\n".format(X.shape, Y.shape, F.shape))
        if len(F.shape) == 3: F = F[0, ...]

        xMin, yMin, xMax, yMax = X[0], Y[0], X[-1], Y[-1]
        sr = int(kwargs.get('sr', 4326))
        
        kwargs['output_info'] = { 
            'bandCount': 1,
            'pixelType': F.dtype.str,
            'nativeExtent': (xMin, yMin, xMax, yMax),
            'extent': (xMin, yMin, xMax, yMax),
            'cellSize': ((xMax-xMin)/X.size, (yMax-yMin)/Y.size),
            'spatialReference': sr,
            'nativeSpatialReference': sr,
            'statistics': (),
            'histogram': (),
            'colormap': (),
            'noData': np.array([256], dtype='u1'),
            'resampling': False
        }

        self.trace("Trace|InterpolateMesh.updateRasterInfo.1|{0}\n".format(kwargs))
        self.interpolant = interpolate.RectBivariateSpline(X, Y, F.T)
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        e = utils.computeMapExtents(tlc, shape, props)
        nRows, nCols = shape if len(shape) == 2 else shape[1:]
        x = np.linspace(e[0], e[2], nCols)
        y = np.linspace(e[1], e[3], nRows)

        self.trace("Trace|InterpolateMesh.updatePixels.1|tlc: {0}|shape: {1}|props: {2}|\n".format(tlc, shape, props))
        self.trace("Trace|InterpolateMesh.updatePixels.2|requestExtent: {0}|\n".format(e))
        self.trace("Trace|InterpolateMesh.updatePixels.3|x: {0}|y: {1}|\n".format(x, y))
        f = self.interpolant(x, y).T

        self.trace("Trace|InterpolateMesh.updatePixels.4|f: {0}|\n".format(f))
        pixelBlocks['output_pixels'] = f.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = np.ones(shape, dtype='u1')
        return pixelBlocks

