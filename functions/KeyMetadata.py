import json


class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata Function"
        self.description = "Override or insert key-metadata of a raster in a function chain."
        self.datasetProps = {}
        self.bandProps = []

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
                'description': "The name of the optional dataset-level key property to override."
            },
            {
                'name': 'value',
                'dataType': 'string',
                'value': None,
                'displayName': "Property Value",
                'required': False,
                'description': "The overriding new value of the dataset-level key property."
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
                'description': ("Key metadata to be injected into the outgoing raster described as a JSON string representing a collection of key-value pairs. "
                                "Learn more by searching for phrase 'Raster Key Properties' at http://resources.arcgis.com.")
            },
    ]

    def getConfiguration(self, **scalars):
        return {
            'invalidateProperties': 8,          # reset any key properties held by the parent function raster dataset
        }

    def updateRasterInfo(self, **kwargs):
        try:
            allProps = json.loads(kwargs.get('json', "{}"))
        except ValueError as e:
            raise Exception(e.message)
             
        self.datasetProps = { k.lower(): v for k, v in allProps.items() }

        # inject name-value pair into bag of properties
        p = kwargs.get('property', "").lower()
        if len(p) > 0:
            self.datasetProps[p] = kwargs.get('value', None)

        # get bandproperties array from original JSON as a list of dictionaries...
        self.bandProps = []
        for d in allProps.get('bandproperties', []):
            self.bandProps.append(
                { k.lower(): v for k, v in d.items() } if isinstance(d, dict) else None)

        # ensure size of bandProps matches input band count
        bandCount = kwargs['raster_info']['bandCount']
        self.bandProps.extend([{} for k in range(0, bandCount-len(self.bandProps))])

        # inject band names into the bandProps dictionary
        b = kwargs.get('bands', "").strip()
        if len(b) > 0:
            bandNames = b.split(',')
            for k in range(0, min(len(self.bandProps), len(bandNames))):
                self.bandProps[k]['bandname'] = bandNames[k]
        
        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        # return keyMetadata dictionary with updated values for entries in [names]...
        properties = self.datasetProps if bandIndex == -1  else self.bandProps[bandIndex]
        if properties is None:
            return keyMetadata

        for name in names:
            if properties.has_key(name):
                v = properties[name]
                keyMetadata[name] = str(v) if isinstance(v, unicode) else v
        
        return keyMetadata
