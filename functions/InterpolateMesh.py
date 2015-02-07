import arcpy
import numpy as np
import ctypes
from scipy import ndimage
from scipy import interpolate

class InterpolateMesh():

    def __init__(self):
        self.name = "Interpolate Mesh Function"
        self.description = ""
        self.X = None
        self.Y = None
        self.emit = ctypes.windll.kernel32.OutputDebugStringA
        self.emit.argtypes = [ctypes.c_char_p]

        
    def getParameterInfo(self):
        return [
            {
                'name': 'v',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Value Raster",
                'description': "",
            },
            {
                'name': 'xf',
                'dataType': 'string',
                'value': r"c:\Users\fero4752\Box Sync\Swap\mesh\lon_rho.tif",
                'required': True,
                'displayName': "X-Coordinates File",
                'description': "",
            },
            {
                'name': 'yf',
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


    def getConfiguration(self, **scalars): 
        return {
          'extractBands': (0, ),                # can only handle a single band raster
          'inheritProperties': 4 | 8,           # inherit everything but the pixel type (1) and NoData (2)
          'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
          'inputMask': True                     # we need the input mask in .updatePixels()
        }


    def updateRasterInfo(self, **kwargs):
        self.X = arcpy.RasterToNumPyArray(kwargs['xf'])[0,:]
        self.Y = arcpy.RasterToNumPyArray(kwargs['yf'])[:,0]
        xMin, yMin, xMax, yMax = np.min(self.X), np.min(self.Y), np.max(self.X), np.max(self.Y)
        kwargs['output_info']['nativeExtent'] = (xMin, yMin, xMax, yMax)
        kwargs['output_info']['extent'] = (xMin, yMin, xMax, yMax)
        kwargs['output_info']['cellSize'] = ((xMax-xMin)/self.X.size, (yMax-yMin)/self.Y.size)

        sr = int(kwargs.get('sr', 4326))
        kwargs['output_info']['nativeSpatialReference'] = sr
        kwargs['output_info']['spatialReference'] = sr
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['resampling'] = False

        self.emit("Trace|InterpolateMesh.updateRasterInfo|{0}\n".format(kwargs))
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        self.emit("Trace|InterpolateMesh.updatePixels|tlc={0}|shape={1}|props={2}\n".format(tlc, shape, props))

        u = np.array(pixelBlocks['v_pixels'], dtype='f4', copy=False)
        u = u.T
        u[u>1000] = 0

        self.emit("Trace|InterpolateMesh.updatePixels|X={0}|Y={1}|Z={2}\n".format(self.X.shape, self.Y.shape, u.shape))
        interpolator = interpolate.RectBivariateSpline(self.X, self.Y, u)

        if len(u.shape) == 2:
            nRows, nCols = u.shape
        else: 
            nRows, nCols = u.shape[1:]

        xCell, yCell = props['cellSize']
        xMin, yMin, xMax, yMax = props['extent']
        xMin += tlc[0] * xCell 
        yMax -= tlc[1] * yCell 

        self.emit("Trace|InterpolateMesh.updatePixels|{0}|{1}\n".format(xMin, yMax))
        x = np.linspace(xMin, xMin+nCols*xCell, nCols)
        y = np.linspace(yMax-nRows*yCell, yMax, nRows)
        self.emit("Trace|InterpolateMesh.updatePixels|x={0}|y={1}\n".format(x, y))
        v = interpolator(x, y).T

        self.emit("Trace|InterpolateMesh.updatePixels|v={0}|\n".format(v))
        pixelBlocks['output_pixels'] = v.astype(props['pixelType'], copy=False)        
        return pixelBlocks

