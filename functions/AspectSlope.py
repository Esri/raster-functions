#--------------------------------------------------------------------------------------------
# Name  	    	: Aspect-Slope Map
# ArcGIS Version	: ArcGIS 10.5
# Script Version	: 20160915
# Name of Company 	: Environmental System Research Institute
# Author        	: ESRI raster solution team
# Purpose 	    	: Create a map that simultaneously displays the aspect (direction)
#                     and slope(steepness) of a continuous surface, such as terrain
#                     as represented in a digital elevation model (DEM).
# Created	    	: 20160915
# LastUpdated  		: 20160915
# Required Argument : Raster.
# Optional Argument : Z-factor.
# Usage         	: To be called as python raster function.
# Copyright	    	: (c) ESRI 2016
# License	    	: ESRI Internal.
#---------------------------------------------------------------------------------------------
from scipy import ndimage
import math
from decimal import *
import numpy as np


class AspectSlope():

    def __init(self):
        self.name = "Aspect-Slope Map."
        self.description = "Aspect-Slope."
        self.prepare()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "Input raster for which to create the aspect-slope map."
            },
            {
                'name': 'zf',
                'dataType': 'numeric',
                'value': 1.,
                'required': False,
                'displayName': "Z-factor",
                'description': ("A multiplication factor that converts the vertical (elevation) values to the linear units of the horizontal (x,y) coordinate system. "
                                "Use larger values to add vertical exaggeration."),
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,
            'inheritProperties': 2 | 4 | 8,         # Inherit all but the pixel type and NoData from the input raster dataset.
            'invalidateProperties': 2 | 4 | 8,          # Invalidate the statistics and histogram on the parent dataset because the pixel values are modified.
            'inputMask': True,
            'resampling': False,
            'padding': 1                                # An input raster mask is not needed in .updatePixels() because the inherited area of NoData are used instead.
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        r = kwargs['raster_info']
        kwargs['output_info']['noData'] = self.assignNoData(r['pixelType']) if not(r['noData']) else r['noData']
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['histogram'] = ()
        colormap = (np.array([19, 21, 22, 23, 24, 25, 26, 27, 28, 31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48], dtype='int32'),
                    np.array([161,152,114,124,140,180,203,197,189,141,61,80,119,192,231,226,214,132,0,0,108,202,255,255,244], dtype='uint8'),
                    np.array([161,181,168,142,117,123,139,165,191,196,171,120,71,77,111,166,219,214,171,104,0,0,85,171,250], dtype='uint8'),
                    np.array([161,129,144,173,160,161,143,138,137,88,113,182,157,156,122,108,94,0,68,192,163,156,104,71,0], dtype='uint8'))  # Colormap RGB values for pixels from 19 - 48.
        kwargs['output_info']['colormap'] = colormap  # Output Colormap values.
        self.prepare(zFactor=kwargs.get('zf', 1.))
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        dem = np.array(pixelBlocks['raster_pixels'], dtype='f4', copy=False)[0]                     # Input pixel array.
        m = np.array(pixelBlocks['raster_mask'], dtype='u1', copy=False)[0]                         # Input raster mask.
        self.noData = self.assignNoData(props['pixelType']) if not(props['noData']) else props['noData']
        xKernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])                                    # Weights for calculation of dz/dx value array.
        yKernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])                                    # Weights for calculation of dz/dy value array.
        temp = np.where(np.not_equal(dem, self.noData), dem, dem)
        p = props['cellSize']
        deltaX = (ndimage.convolve(temp, xKernel)) / 8                                              # dz/dx values.
        deltaY = (ndimage.convolve(temp, yKernel)) / 8                                              # dz/dy values.
        if (p[0] <= 0) | (p[1] <= 0):
            raise Exception("Input raster cell size is invalid.")
        dx = deltaX / p[0]                                                                          # Divide by cell size.
        dy = deltaY / p[1]
        dx = dx * self.zf                                                                           # Multiply by z-factor.
        dy = dy * self.zf
        slopeTangent = (np.sqrt((dx * dx) + (dy * dy))) * 100                                       # Slope Calculation.
        aspect = 57.29578 * np.arctan2(deltaX, (-1) * deltaY)                                       # Aspect Calculation.
        aspect[(aspect < 0.00)] = (360.00 - (90.00 - aspect[(aspect < 0.00)])) + 90
        aspect[slopeTangent == 0] = -1                                                              # Aspect assigned -1 for slope values 0.
        slopeTangent[(slopeTangent >= 0) & (slopeTangent < 5)] = -10
        slopeTangent[(slopeTangent >= 5) & (slopeTangent < 20)] = -20
        slopeTangent[(slopeTangent >= 20) & (slopeTangent < 40)] = -30
        slopeTangent[(slopeTangent >= 40)] = -40
        slopeTangent[(slopeTangent == -10)] = 10
        slopeTangent[(slopeTangent == -20)] = 20
        slopeTangent[(slopeTangent == -30)] = 30
        slopeTangent[(slopeTangent == -40)] = 40
        aspect[(aspect >= -1) & (aspect <= 22.5)] = 1
        aspect[(aspect > 22.5) & (aspect <= 67.5)] = 2
        aspect[(aspect > 67.5) & (aspect <= 112.5)] = 3
        aspect[(aspect > 112.5) & (aspect <= 157.5)] = 4
        aspect[(aspect > 157.5) & (aspect <= 202.5)] = 5
        aspect[(aspect > 202.5) & (aspect <= 247.5)] = 6
        aspect[(aspect > 247.5) & (aspect <= 292.5)] = 7
        aspect[(aspect > 292.5) & (aspect <= 337.5)] = 8
        aspect[(aspect > 337.5) & (aspect <= 360)] = 1
        finalArray = np.add(slopeTangent, aspect)                                                   # Add the slope and aspect arrays.
        finalArray[(finalArray >= 11) & (finalArray <= 18)] = 19
        pixelBlocks['output_pixels'] = finalArray[1:-1, 1:-1].astype(props['pixelType'])
        pixelBlocks['output_mask'] = \
            m[:-2, :-2]  & m[1:-1, :-2]  & m[2:, :-2]  \
            & m[:-2, 1:-1] & m[1:-1, 1:-1] & m[2:, 1:-1] \
            & m[:-2, 2:] & m[1:-1, 2:] & m[2:, 2:]

        return pixelBlocks

    def assignNoData(self, pixelType):
                                                        # assign noData depending on input pixelType
        if pixelType == 'f4':
            return np.array([-3.4028235e+038, ])        # float 32 bit
        elif pixelType == 'i4':
            return np.array([-65536, ])                 # signed integer 32 bit
        elif pixelType == 'i2':
            return np.array([-32768, ])                 # signed integer 16 bit
        elif pixelType == 'i1':
            return np.array([-256, ])                   # signed integer 8 bit
        elif pixelType == 'u4':
            return np.array([65535, ])                  # unsigned integer 32 bit
        elif pixelType == 'u2':
            return np.array([32767, ])                  # unsigned integer 16 bit
        elif pixelType == 'u1':
            return np.array([255, ])                    # unsigned integer 8 bit

    def prepare(self, zFactor=1):
        self.zf = zFactor
