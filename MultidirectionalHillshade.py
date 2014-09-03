import numpy as np
import math 


# TODO: Enable support for padding
# TODO: Enable different flavors of z-factor

class MultidirectionalHillshade():


    def __init__(self):
        self.name = "Multidirectional Hillshade Function"
        self.description = ""
        self.trigLookup = None
        self.azimuths     = (315.0, 270.0, 225.0, 360.0, 180.0,   0.0)
        self.elevations   = ( 60.0,  60.0, 60.0,   60.0,  60.0,   0.0)
        self.weights      = (0.167, 0.278, 0.167, 0.111, 0.056, 0.222)
        self.factors      = ()


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
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['colormap'] = ()

        if kwargs['raster_info']['bandCount'] > 1:
            raise Exception("Input raster has more than one band. Only single-band raster datasets are supported")

        cellSize = kwargs['raster_info']['cellSize']
        self.factors = 1.0 / (8 * cellSize[0]), 1.0 / (8 * cellSize[1])

        n = len(self.azimuths)
        self.trigLookup = np.ndarray([n, 3])                        # pre-compute for use in .getHillshade() via .updatePixels()
        for i in range(0, n - 1):
            Z = (90.0 - self.elevations[i]) * math.pi / 180.0       # Sun Zenith Angle in Radians
            A = (90.0 - self.azimuths[i]) * math.pi / 180.0         # Sun Azimuth arithmetic angle (radians)
            sinZ = math.sin(Z)
            self.trigLookup[i, 0] = math.cos(Z)
            self.trigLookup[i, 1] = sinZ * math.sin(A)
            self.trigLookup[i, 2] = sinZ * math.cos(A)

        return kwargs


    def updatePixels(self, tlc, size, props, **pixelBlocks):
        # cf: http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html
        v = np.array(pixelBlocks['raster_pixels'], dtype='f4')
        dx, dy = np.gradient(v)
        dx = dx * self.factors[0]
        dy = dy * self.factors[1]

        outBlock = self.weights[0] * self.getHillshade(v, 0, dx, dy)
        for i in range(1, 5):
            outBlock = outBlock + (self.weights[i] * self.getHillshade(v, i, dx, dy))

        pixelBlocks['output_pixels'] = outBlock[1:-1, 1:-1].astype(props['pixelType'])

        m = np.array(pixelBlocks['raster_mask'], dtype='u1')
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


    def getHillshade(self, pixelBlock, index, dx, dy):
        # cf: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//009z000000z2000000.htm
        cosZ = self.trigLookup[index, 0]
        sinZsinA = self.trigLookup[index, 1]
        sinZcosA = self.trigLookup[index, 2]
        return np.clip(255 * (cosZ + dy*sinZsinA - dx*sinZcosA) / np.sqrt(1. + (dx*dx + dy*dy)), 0.0, 255.0)

