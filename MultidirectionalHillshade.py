#http://www.uoguelph.ca/~hydrogeo/Whitebox/Help/Hillshade.html
#https://github.com/rveciana/geoexamples/blob/master/python/shaded_relief/hillshade.py
#http://geoexamples.blogspot.com/2014/03/shaded-relief-images-using-gdal-python.html
#http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//009z000000z2000000.htm

import numpy as np
import math 


class MultidirectionalHillshade():


    def __init__(self):
        self.name = "Multidirectional Hillshade Function"
        self.description = ""
        self.lookup = None
        self.constants = (0.167, 0.278, 0.167, 0.111, 0.056, 0.222)


    def getParameterInfo(self):
        return [{
                'name': 'raster',
                'dataType': 2,
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary input raster where pixel values represent elevation.",
            },]


    def getConfiguration(self, **scalars): 
        return {
          'extractBands': (0,),             # we only need the first band.  Comma after zero ensures it's a tuple.
          'inheritProperties': 4 | 8,       # inherit everything but the pixel type (1) and NoData (2)
          'invalidateProperties': 2 | 4 | 8 # invalidate these aspects because we are modifying pixel values and updating key properties.
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = '8_BIT_UNSIGNED'
        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['colormap'] = ()

        cellSize = kwargs['raster_info']['cellSize']
        coefficients = (0.167, 0.278, 0.167, 0.111, 0.056, 0.222)
        azimuths     = (315.0, 270.0, 225.0, 360.0, 180.0,   0.0)
        elevations   = ( 60.0,  60.0, 60.0,   60.0,  60.0,   0.0)
        n = len(coefficients)

        """
        Things to lookup:
            SunA: Sun Azimuth in degrees
            SunZ: Sun Elevation in degrees
            A = Sun Azimuth arithmetic angle (radians)
            Z: Sun Zenith Angle in Radians
            sinZ = sin(Z) 
            sinA = sin(A)
            cosZ = cos(Z)
            sinZsinA = sin(Z) * sin(A)
            sinZcosA = sin(Z) * cos(A)
            Coefficient
            xScaling
            yScaling
        """
        self.lookup = np.ndarray([n, 12])
        for i in range(0, n - 1):
            sunA, sunZ = azimuths[i], elevations[i]
            A = (90.0 - sunA) * math.pi / 180.0
            Z = (90.0 - sunZ) * math.pi / 180.0
            sinZ = math.sin(Z)
            sinA = math.sin(A)
            sinA = math.sin(A)
            cosZ = math.cos(Z)
            self.lookup[i, 0] = sunA
            self.lookup[i, 1] = sunZ
            self.lookup[i, 2] = A
            self.lookup[i, 3] = Z
            self.lookup[i, 4] = sinZ
            self.lookup[i, 5] = sinA
            self.lookup[i, 6] = cosZ
            self.lookup[i, 7] = sinZ * sinA
            self.lookup[i, 8] = sinZ * math.cos(A)
            self.lookup[i, 9] = coefficients[i]
            self.lookup[i, 10] = 1.0 / (8 * cellSize[0])
            self.lookup[i, 11] = 1.0 / (8 * cellSize[1])

        return kwargs

    def getWeightedHillshade(self, pixelBlock, index, dx, dy):
        slope = math.pi / 2.0 - np.arctan(np.sqrt(dx*dx + dy*dy))
        aspect = np.arctan2(-dx, dy)
        azimuthrad = self.lookup[index, 0] * math.pi / 180.0
        altituderad = self.lookup[index, 1] * math.pi / 180.0

        shaded = math.sin(altituderad) * np.sin(slope) + math.cos(altituderad) * np.cos(slope) * np.cos(azimuthrad - aspect)
        return 255 * self.lookup[index, 9] * (shaded + 1) / 2

        #cosZ = self.lookup[index, 6]
        #sinZsinA = self.lookup[index, 7]
        #sinZcosA = self.lookup[index, 8]
        #c = self.lookup[index, 9]

        #d2 = dx*dx + dy*dy
        #cosDelta = sinZsinA * dy - sinZcosA * dx
        #return c * np.clip(255 * (cosZ + cosDelta) / np.sqrt(1 + d2), 0.0, 255.0)

    def updatePixels(self, **pixelBlocks):
        if not pixelBlocks.has_key("raster_pixels"):
            raise Exception("No input raster was provided.")

        v = np.array(pixelBlocks['raster_pixels'], dtype='float')
        dx, dy = np.gradient(v)

        outBlock = self.getWeightedHillshade(v, 0, dx, dy)
        for i in range(1, 5):
            outBlock = outBlock + self.getWeightedHillshade(v, i, dx, dy)

        np.copyto(pixelBlocks['output_pixels'], outBlock, casting='unsafe')     # copy local array to output pixel block.
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == - 1:                             # dataset-level properties           
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Hillshade'
        return keyMetadata
