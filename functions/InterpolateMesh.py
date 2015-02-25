import arcpy
import numpy as np
from scipy import ndimage
from scipy import interpolate
import utils
from matplotlib import pyplot as plt
import pyproj

class InterpolateMesh():

    def __init__(self):
        self.name = "Interpolate Mesh Function"
        self.description = ""
        self.interpolant = None
        self.trace = utils.getTraceFunction()
        self.projection = utils.Projection()
        self.meshSR = 0

        
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

        if F.ndim == 3: F = F[0, ...]       # handles only single band in the value-raster
        F = np.flipud(F)

        if X.ndim != 2 or Y.ndim != 2:
            raise Exception("X- and Y-coordinates must be represented by single-band rasters.")

        X, Y = X[0, ...].squeeze(), Y[..., 0::-1].squeeze()     # flipping Y-vector
        xMin, yMin, xMax, yMax = X[0], Y[0], X[-1], Y[-1]
        noData = kwargs['f_info'].get('noData', ())
        if not noData is None and len(noData) >= 1:
            noData = noData[0]
            F[F == noData] = -9999

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
            'noData': (noData, ),
            'resampling': True
        }

        self.meshSR = sr
        self.trace("Trace|InterpolateMesh.updateRasterInfo.1|{0}|\n".format(kwargs))
        self.interpolant = interpolate.RectBivariateSpline(Y, X, F)
        return kwargs


    def selectRasters(self, tlc, shape, props):
        return ()
    

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        rasterSR = props['spatialReference']
        if rasterSR != self.meshSR:
            self.projection.transform(self.meshSR, rasterSR, )
            
        nRows, nCols = shape if len(shape) == 2 else shape[1:]
        e = utils.computeMapExtents(tlc, shape, props)
        f = self.interpolant(np.linspace(e[1], e[3], nRows), np.linspace(e[0], e[2], nCols))
        pixelBlocks['output_pixels'] = f.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = np.ones(shape, dtype='u1')

        #plt.imshow(f, interpolation='nearest')
        #plt.show()
        #self.trace("Trace|InterpolateMesh.updatePixels.1|X: {0}|\n".format(np.linspace(e[0], e[2], nCols)))
        #self.trace("Trace|InterpolateMesh.updatePixels.1|Y: {0}|\n".format(np.linspace(e[1], e[3], nRows)))
        #self.trace("Trace|InterpolateMesh.updatePixels.1|F: {0}|\n".format(f))

        return pixelBlocks


    def isLicensed(self, **productInfo): 
        return {
            'okToRun': utils.isProductVersionOK(productInfo, 10, 3.1, 4919),
            'message': "The python raster function is only compatible with ArcGIS 10.3.1 build 4919 or above.",
        }
