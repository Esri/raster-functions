import ast


class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata Function"
        self.description = "Override key metadata in a function chain."
        self.props = None

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
            },
            {
                'name': 'json',
                'dataType': 'string',
                'value': '',
                'displayName': "Metadata JSON",
                'required': False,
                'description': ""
            },
    ]

    def getConfiguration(self, **scalars):
        return {
            'invalidateProperties': 8,          # reset any key properties held by the parent function raster dataset
        }

    def updateRasterInfo(self, **kwargs):
        jsonInput = kwargs.get('json', "")

        # band specific metadata properties
        bandSpecificProperties = ["wavelengthmin", "wavelengthmax", "reflectancebias", "sourcebandindex",
                                  "reflectancegain", "radiancegain", "radiancebias", "solarirradiance"]

        if len(jsonInput) > 0:
            self.props = ast.literal_eval(kwargs.get('json', ""))

        if self.props is None:
            self.props = {}

        if not 'bandproperties' in self.props.keys():
            self.props['bandproperties'] = []

        bandCount = kwargs['raster_info']['bandCount']
        bandProps = self.props['bandproperties']
        bandProps.extend([{} for k in range(0, bandCount-len(bandProps))])

        # band names
        bandNamesTemp = kwargs.get('bands', "").strip()

        if len(bandNamesTemp) > 0:
            bandNames = bandNamesTemp.split(',')
            for x in range(0, min(len(bandProps), len(bandNames))):
                bandProps[x]['bandname'] = bandNames[x]

        propertyName = kwargs.get('property', "").lower().strip()

        if len(propertyName) > 0:              # inject name-value pair into bag of properties
            # band specific properties (per band)
            if propertyName in bandSpecificProperties:
                propertyValues = kwargs.get('value', "").split(",")
                for x in range(0, min(len(propertyValues), len(bandNames))):
                    bandProps[x][propertyName] = propertyValues[x]

            # raster specific properties
            else:
                self.props[propertyName] = kwargs.get('value', "")

        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if self.props is None:
            return keyMetadata

        properties = self.props
        if bandIndex != -1:
            if 'bandproperties' not in properties.keys():
                return keyMetadata
            bandProps = self.props['bandproperties']

            if not bandProps or len(bandProps) < bandIndex + 1:
                return keyMetadata
            properties = bandProps[bandIndex]

        for name in names:
           if name in properties.keys():
                assign = properties[name]
                keyMetadata[name] = str(assign) if isinstance(assign, unicode) else assign

        return keyMetadata
