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


class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata"
        self.description = "Override key metadata in a function chain."
        self.propertyName = ''
        self.propertyValue = None
        self.bandNames = []


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': '',
                'displayName': "Raster",
                'required': True,
                'description': "The primary raster input."
            },
            {
                'name': 'property',
                'dataType': 'string',
                'value': self.propertyName,
                'displayName': "Property Name",
                'required': False,
                'description': "The name of the optional key metadata to override."
            },
            {
                'name': 'value',
                'dataType': 'string',
                'value': self.propertyValue,
                'displayName': "Property Value",
                'required': False,
                'description': "The overriding new value of the key metadata."
            },
            {
                'name': 'bands',
                'dataType': 'string',
                'value': '',
                'displayName': "Band Names",
                'required': False,
                'description': "A comma-separated string representing updated band names."
            }
        ]


    def getConfiguration(self, **scalars):
        return { 
            'invalidateProperties': 8,          # reset any key properties held by the parent function raster dataset
            'inputMask': False
        }


    def updateRasterInfo(self, **kwargs):
        self.propertyName = kwargs['property']  # remember these user-specified scalar inputs
        self.propertyValue = kwargs['value']
        self.bandNames = kwargs['bands'].split(',')
        return kwargs


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
           if len(self.propertyName) > 0:
                keyMetadata[self.propertyName] = self.propertyValue
        elif bandIndex < len(self.bandNames):
            keyMetadata['bandname'] = self.bandNames[bandIndex]

        return keyMetadata
