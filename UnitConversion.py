"""
COPYRIGHT 1995-2004 ESRI

TRADE SECRETS: ESRI PROPRIETARY AND CONFIDENTIAL
Unpublished material - all rights reserved under the
Copyright Laws of the United States.

For additional information, contact:
Environmental Systems Research Institute, Inc.
Attn: Contracts Dept
380 New York Street
redlands, California, USA 92373
email: contracts@esri.com
"""

import numpy as np


class UnitConversion():
    def __init__(self):
        self.name = ""
        self.description = ""


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster",
                'description': "The primary input raster."
            },
            {
                'name': 'datetime',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Date and time",
                'description': ""
            },
        ]


    def getConfiguration(self, **scalars):
        return {
          'compositeRasters': False,            # input is a single raster, band compositing doesn't apply.
          'inheritProperties': 1 | 2 | 4 | 8,   # inherit everything
          'invalidateProperties': 2 | 4,        # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['statistics'] = ()        # clear stats.
        kwargs['output_info']['histogram'] = ()         # clear histogram.
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        inBlock = pixelBlocks['raster_pixels']                  # get the input raster pixel block
        pixelBlocks['output_pixels'] = inBlock.astype(props['pixelType'])
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['units'] = ''
        return keyMetadata
