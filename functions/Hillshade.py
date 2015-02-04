from scipy import ndimage
import numpy as np
import math 

class Hillshade():

    def __init__(self):
        self.name = "Hillshade Function"
        self.description = ""
        self.prepare()   

  
    def prepare(self, azimuth=315., elevation=45.,
                zFactor=1., cellSizeExponent=0.664, cellSizeFactor=0.024, cellSize=None, sr=None):
        Z = (90. - elevation) * math.pi / 180.   # solar _zenith_ angle in radians
        A = (90. - azimuth) * math.pi / 180.     # solar azimuth _arithmetic_ angle in radians
        sinZ = math.sin(Z)
        self.cosZ = math.cos(Z)
        self.sinZsinA = sinZ * math.sin(A)
        self.sinZcosA = sinZ * math.cos(A)
        self.xKernel = [[1, 0, -1], [2, 0, -2], [1, 0, -1]]
        self.yKernel = [[1, 2, 1], [0, 0, 0], [-1, -2, -1]]

        m = 1.
        if math.fabs(zFactor - 1.) <= 0.0001 and sr == 4326: 
            m = 1.11e5  # multiplicative factor for converting cell size in degrees to meters (defaults to 1)

        if not cellSize is None and len(cellSize) == 2:
            self.xScale = (zFactor + (math.pow(cellSize[0]*m, cellSizeExponent) * cellSizeFactor)) / (8. * cellSize[0]*m), 
            self.yScale = (zFactor + (math.pow(cellSize[1]*m, cellSizeExponent) * cellSizeFactor)) / (8. * cellSize[1]*m), 
        else:
            self.xScale, self.yScale = 1., 1.


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
                'description': "The multiplicative factor that converts elevation values to the units of the horizontal (xy-) coordinate system.",
            },
            {
                'name': 'ce',
                'dataType': 'numeric',
                'value': 0.664,
                'required': False,
                'displayName': "Cell Size Exponent",
                'description': "",
            },
            {
                'name': 'cf',
                'dataType': 'numeric',
                'value': 0.024,
                'required': False,
                'displayName': "Cell Size Factor",
                'description': "",
            },
        ]


    def getConfiguration(self, **scalars): 
        return {
          'extractBands': (0,),                 # we only need the first band.  Comma after zero ensures it's a tuple.
          'inheritProperties': 4 | 8,           # inherit everything but the pixel type (1) and NoData (2)
          'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 1,                         # one extra on each each of the input pixel block
          'inputMask': True                     # we need the input mask in .updatePixels()
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
                     cellSize=r['cellSize'],
                     sr=r['spatialReference'])
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = np.array(pixelBlocks['raster_pixels'], dtype='f4', copy=False)
        m = np.array(pixelBlocks['raster_mask'], dtype='u1', copy=False)

        dx, dy = self.computeGradients(v)
        outBlock = self.computeHillshade(dx, dy)
        pixelBlocks['output_pixels'] = outBlock[1:-1, 1:-1].astype(props['pixelType'], copy=False)

        # cf: http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html
        pixelBlocks['output_mask'] = \
            m[:-2,:-2]  & m[1:-1,:-2]  & m[2:,:-2]  \
          & m[:-2,1:-1] & m[1:-1,1:-1] & m[2:,1:-1] \
          & m[:-2,2:]   & m[1:-1,2:]   & m[2:,2:]

        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties           
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Hillshade'
        return keyMetadata


    def computeGradients(self, pixelBlock):
        dx = ndimage.convolve(pixelBlock, self.xKernel) * self.xScale
        dy = ndimage.convolve(pixelBlock, self.yKernel) * self.yScale
        return (dx, dy)


    def computeHillshade(self, dx, dy):
        # cf: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//009z000000z2000000.htm
        return np.clip(255 * (self.cosZ + dy*self.sinZsinA - dx*self.sinZcosA) / np.sqrt(1. + (dx*dx + dy*dy)), 0., 255.)

