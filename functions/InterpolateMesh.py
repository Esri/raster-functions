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
                'dataType': 'raster',
                'value': None, 
                'required': True,
                'preloadPixels': True,
                'displayName': "Value Raster",
                'description': "Path to the image file containing pixel values at each grid point.",
            },
            {
                'name': 'x',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'preloadPixels': True,
                'displayName': "X-Coordinates Raster",
                'description': "First dimension of the XY meshgrid.",
            },
            {
                'name': 'y',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'preloadPixels': True,
                'displayName': "Y-Coordinates Raster",
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
        X, Y, F = kwargs.get('x_pixels', None), kwargs.get('y_pixels', None), kwargs.get('f_pixels', None)

        np.ndarray.ndim
        if F.ndim == 3: F = F[0, ...]                           # handles single band in the value-raster
        if X.ndim != 2 or Y.ndim != 2:
            raise Exception("X- and Y-coordinates must be represented by single-band rasters.")

        X, Y = X[0, ...].squeeze(), Y[..., 0::-1].squeeze()
        self.trace("Trace|InterpolateMesh.updateRasterInfo|X: {0}|Y: {1}|\n".format(X, Y))
        xMin, yMin, xMax, yMax = X[0], Y[0], X[-1], Y[-1]
        sr = int(kwargs.get('sr', 4326))
        noData = kwargs['f_info'].get('noData', ())
        noData = noData[0] if len(noData) >= 1 else -9999.0

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
            'noData': (noData, ),
            'resampling': True
        }

        F[F == noData] = 100
        self.trace("Trace|InterpolateMesh.updateRasterInfo.2|F: {0}|\n".format(F))
        self.interpolant = interpolate.RectBivariateSpline(Y, X, F)
        return kwargs


    def selectRasters(self, tlc, shape, props):
        return ()
    

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        nRows, nCols = shape if len(shape) == 2 else shape[1:]
        e = utils.computeMapExtents(tlc, shape, props)

        f = self.interpolant(np.linspace(e[1], e[3], nRows), np.linspace(e[0], e[2], nCols))
        pixelBlocks['output_pixels'] = np.flipud(f).astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = np.ones(shape, dtype='u1')
        return pixelBlocks


    def isLicensed(self, **productInfo): 
        v = productInfo['major']*1.e+10 + productInfo['minor']*1.e+7 + productInfo['build']
        return {
            'okToRun': v >= 10*1e+10 + 3.0*1e+7 + 4914,
            'message': "The python raster function is only compatible with ArcGIS 10.3.1 build 4914 or above",
        }
