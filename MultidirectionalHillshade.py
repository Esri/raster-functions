#------------------------------------------------------------------------------
# Copyright 2014 Esri
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

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

    def updatePixels(self, **pixelBlocks):
        v = np.array(pixelBlocks['raster_pixels'], dtype='float')
        dx, dy = np.gradient(v)
        dx = dx * self.factors[0]
        dy = dy * self.factors[1]

        outBlock = self.weights[0] * self.getHillshade(v, 0, dx, dy)
        for i in range(1, 5):
            outBlock = outBlock + (self.weights[i] * self.getHillshade(v, i, dx, dy))

        np.copyto(pixelBlocks['output_pixels'], outBlock, casting='unsafe')     # copy local array to output pixel block.
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == - 1:                            # dataset-level properties           
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

