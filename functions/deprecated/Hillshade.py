from scipy import ndimage
import numpy as np
import math
from utils import computeCellSize, Projection, isGeographic, projectCellSize


class Hillshade():

    def __init__(self):
        self.name = "Hillshade Function"
        self.description = ""
        self.prepare()
        self.proj = Projection()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster where pixel values represent elevation.",
            },
            {
                'name': 'zf',
                'dataType': 'numeric',
                'value': 1.,
                'required': False,
                'displayName': "Z Factor",
                'description': ("The multiplicative factor that converts elevation values to the units of the horizontal (xy-) coordinate system. "
                                "Or use larger values to add vertical exaggeration."),
            },
            {
                'name': 'ce',
                'dataType': 'numeric',
                'value': 0.664,
                'required': False,
                'displayName': "Cell Size Exponent",
                'description': ("The exponent (ce) on the cell-size (p) towards dynamically adjusting the Z-Factor (zf). "
                                "zf <- zf + cf*[p^ce]/8p."),
            },
            {
                'name': 'cf',
                'dataType': 'numeric',
                'value': 0.024,
                'required': False,
                'displayName': "Cell Size Factor",
                'description': ("The scaling (cf) applied to the cell-size (p) towards dynamically adjusting the Z-Factor (zf). "
                                "Specify zero to disable dynamic scaling. "
                                "zf <- zf + cf*[p^ce]/8p."),
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'extractBands': (0,),                 # we only need the first band.  Comma after zero ensures it's a tuple.
            'inheritProperties': 4 | 8,           # inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
            'padding': 1,                         # one extra on each each of the input pixel block
            'inputMask': True,                    # we need the input mask in .updatePixels()
            'resampling': True                   # Resampling set explicitly to False
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = ({'minimum': 0., 'maximum': 255.}, )
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['colormap'] = ()

        r = kwargs['raster_info']
        if r['bandCount'] > 1:
            raise Exception("Input raster has more than one band. Only single-band raster datasets are supported")

        self.prepare(zFactor=kwargs.get('zf', 1.),
                     cellSizeExponent=kwargs.get('ce', 0.664),
                     cellSizeFactor=kwargs.get('cf', 0.024),
                     sr=r['spatialReference'])
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = np.array(pixelBlocks['raster_pixels'], dtype='f4', copy=False)[0]
        m = np.array(pixelBlocks['raster_mask'], dtype='u1', copy=False)[0]

        dx, dy = self.computeGradients(v, props)
        outBlock = self.computeHillshade(dx, dy)

        pixelBlocks['output_pixels'] = outBlock[1:-1, 1:-1].astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = \
            m[:-2, :-2]  & m[1:-1, :-2]  & m[2:, :-2]  \
          & m[:-2, 1:-1] & m[1:-1, 1:-1] & m[2:, 1:-1] \
          & m[:-2, 2:]   & m[1:-1, 2:]   & m[2:, 2:]
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Hillshade'
        return keyMetadata

    # ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
    # other public methods...

    def prepare(self, azimuth=315., elevation=45., zFactor=1., cellSizeExponent=0.664, cellSizeFactor=0.024, sr=None):
        Z = (90. - elevation) * math.pi / 180.   # solar _zenith_ angle in radians
        A = (90. - azimuth) * math.pi / 180.     # solar azimuth _arithmetic_ angle in radians
        sinZ = math.sin(Z)
        self.cosZ = math.cos(Z)
        self.sinZsinA = sinZ * math.sin(A)
        self.sinZcosA = sinZ * math.cos(A)
        self.xKernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])
        self.yKernel = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
        self.zf = zFactor
        self.ce = cellSizeExponent
        self.cf = cellSizeFactor
        self.sr = sr

    def computeGradients(self, pixelBlock, props):
        # pixel size in input raster SR...
        p = props['cellSize'] if self.sr is None else projectCellSize(props['cellSize'], props['spatialReference'], self.sr, self.proj)
        if p is not None and len(p) == 2:
            p = np.multiply(p, 1.11e5 if isGeographic(self.sr) else 1.)   # conditional degrees to meters conversion
            xs, ys = (self.zf + (np.power(p, self.ce) * self.cf)) / (8*p)
        else:
            xs, ys = 1., 1.         # degenerate case. shouldn't happen.
        return (ndimage.convolve(pixelBlock, self.xKernel)*xs, ndimage.convolve(pixelBlock, self.yKernel)*ys)

    def computeHillshade(self, dx, dy):
        return np.clip(255 * (self.cosZ + dy*self.sinZsinA - dx*self.sinZcosA) / np.sqrt(1. + (dx*dx + dy*dy)), 0., 255.)

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1]. Esri (2013): ArcGIS Resources. How Hillshade works.
    http://resources.arcgis.com/en/help/main/10.2/index.html#//009t0000004z000000

    [2]. Esri (2013): ArcGIS Resources. Hillshade function.
    http://resources.arcgis.com/en/help/main/10.2/index.html#//009z000000z2000000

    [3]. SciPy.org: Array Indexing.
    http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html

    [4]. Burrough, P. A. and McDonell, R. A., 1998.
    Principles of Geographical Information Systems. Oxford University Press, New York, 190 pp.

"""
