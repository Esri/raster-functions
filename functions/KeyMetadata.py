import json
from utils import Trace


class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata Function"
        self.description = "Override key metadata in a function chain."
        self.datasetProps = {}
        self.bandProps = []
        self.trace = Trace()

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
        try:
            allProps = json.loads(kwargs.get('json', "{}"))
        except ValueError as e:
            raise Exception(e.message)
             
        self.datasetProps = { k.lower(): v for k, v in allProps.items() }

        self.bandProps = []
        for d in allProps.get('bandproperties', []):
            self.bandProps.append({ k.lower(): v for k, v in d.items() } if isinstance(d, dict) else None)

        # inject name-value pair into bag of properties
        p = kwargs.get('property', "").lower()
        if len(p) > 0:
            self.datasetProps[p] = kwargs.get('value', None)

        # ensure size of bandProps matches input band count
        bandCount = kwargs['raster_info']['bandCount']
        self.bandProps.extend([{} for k in range(0, bandCount-len(self.bandProps))])

        # inject band names into the bandProps dictionary
        b = kwargs.get('bands', "").strip()
        if len(b) > 0:
            bandNames = b.split(',')
            for k in range(0, min(len(self.bandProps), len(bandNames))):
                self.bandProps[k]['bandname'] = bandNames[k]
        
        self.trace.log("{0}|{1}|{2}".format("KeyMetadata.updateRasterInfo", "dataset", self.datasetProps))
        self.trace.log("{0}|{1}|{2}".format("KeyMetadata.updateRasterInfo", "bands", self.bandProps))
        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        properties = self.datasetProps
        if bandIndex != -1:
            properties = None if not self.bandProps or len(self.bandProps) < bandIndex + 1 else self.bandProps[bandIndex]

        if properties is None:
            return keyMetadata

        for name in names:
            if properties.has_key(name):
                v = properties[name]
                keyMetadata[name] = str(v) if isinstance(v, unicode) else v
        
        self.trace.log("{0}|{1}".format("KeyMetadata.updateKeyMetadata", keyMetadata))
        return keyMetadata
