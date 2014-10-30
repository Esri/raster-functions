class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata Function"
        self.description = "Override key metadata in a function chain."
        self.propertyName = ''
        self.propertyValue = None
        self.bandNames = []


    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'displayName': "Raster",
                'required': True,
                'description': "The primary raster input."
            },
            {
                'name': 'property',
                'dataType': 'string',
                'value': '',
                'displayName': "Property Name",
                'required': False,
                'description': "The name of the optional key metadata to override."
            },
            {
                'name': 'value',
                'dataType': 'string',
                'value': None,
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
        }


    def updateRasterInfo(self, **kwargs):
        self.propertyName = kwargs.get('property', "")  # remember these user-specified scalar inputs
        self.propertyValue = kwargs.get('value', "")

        self.bandNames = []
        b = kwargs.get('bands', "").strip()
        if len(b) > 0:
            self.bandNames = b.split(',')

        return kwargs


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
           if len(self.propertyName) > 0:
                keyMetadata[self.propertyName] = self.propertyValue
        elif bandIndex < len(self.bandNames):
            keyMetadata['bandname'] = self.bandNames[bandIndex]

        return keyMetadata
