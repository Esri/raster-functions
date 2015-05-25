import json
from utils import Trace


class KeyMetadata():

    def __init__(self):
        self.name = "Key Metadata Function"
        self.description = "Override key metadata in a function chain."
        self.props = None
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
        self.props = json.loads(kwargs.get('json', ""))
        if self.props is None:
            self.props = {}

        p = kwargs.get('property', "").lower()
        if len(p) > 0:                          # inject name-value pair into bag of properties
            self.props[p] = kwargs.get('value', "")

        if not 'bandproperties' in self.props.keys():
            self.props['bandproperties'] = []   # 

        bandCount = kwargs['raster_info']['bandCount']
        bandProps = self.props['bandproperties']
        bandProps.append([{} for k in range(0, bandCount-len(bandProps))])

        b = kwargs.get('bands', "").strip()
        if len(b) > 0:
            k = 0
            bandNames = b.split(',')
            for k in range(0, min(len(bandProps), len(bandNames))):
                bandProps[k]['bandname'] = bandNames[k]
        
        self.trace.log("{0}|{1}".format("KeyMetadata.updateRasterInfo", self.props))
        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if self.props is None:
            return keyMetadata
        
        props = self.props
        if bandIndex != -1:
            if 'bandproperties' not in self.props.keys():
                return keyMetadata
            bandProps = self.props['bandproperties']
            if not bandProps or len(bandProps) < bandIndex + 1:
                return keyMetadata
            props = bandProps[bandIndex]

        for name in names:
            if name in props.keys():
                v = props[name]
                keyMetadata[name] = str(v) if isinstance(v, unicode) else v
        
        self.trace.log("{0}|{1}".format("KeyMetadata.updateKeyMetadata", keyMetadata))
        return keyMetadata
