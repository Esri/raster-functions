import numpy as np
import json
from utils import ZonalAttributesTable, loadJSON

class ZonalRemap():

    def __init__(self):
        self.name = "Zonal Remap"
        self.description = ("Remap pixels in a raster based on spatial zones "
                            "defined by another raster, and a zone-dependent "
                            "value mapping defined by a table.")
        self.ztMap = {}                 # zonal thresholds { zoneId:[[zMin,zMax,zVal], ...], ... }
        self.ztTable = None             # valid only if parameter 'ztable' is not a JSON string (but path or URL)
        self.background = 0
        self.defaultTarget = 255
        self.whereClause = None


    def getParameterInfo(self):
        return [
            {
                'name': 'vraster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary single-band input raster."
            },
            {
                'name': 'zraster',
                'dataType': 'raster',
                'value': None,
                'required': False,
                'displayName': "Zone Raster",
                'description': ("The single-band zone raster where each pixel contains "
                                "the zone ID associated with the location.")
            },
            {
                'name': 'ztable',
                'dataType': 'string',
                'value': None,
                'required': True,
                'displayName': "Zonal Thresholds Table",
                'description': ("The threshold map specified as a JSON string, "
                                "a path to a local feature class or table, or a URL to a feature service layer. "
                                "In JSON, it's described as a collection of mapping from zone IDs to an "
                                "array of intervals (zmin-zmax) and the corresponding target value (zval), "
                                "like this: { zoneId:[[zmin,zmax,zval], ...], ... } ")
            },
            {
                'name': 'zid',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Zone ID Field Name",
                'description': ("Name of the field containing the Zone ID values. "
                                "This is only applicable if the 'Zonal Thresholds' parameter contains path to a table "
                                "or a URL to a feature service.")
            },
            {
                'name': 'zmin',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Minimum Value Field Name",
                'description': ("Name of the field containing the minimum value above which an input pixel gets remapped. "
                                "If left unspecified--or if the field value is null--pixel values are not tested for minimum. "
                                "This is only applicable if the 'Zonal Thresholds Table' parameter contains path to a table "
                                "or a URL to a feature service.")
            },
            {
                'name': 'zmax',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Maximum Value Field Name",
                'description': ("Name of the field containing the maximum value below which an input pixel gets remapped. "
                                "If left unspecified--or if the field value is null--pixel values are not tested for maximum. "
                                "This is only applicable if the 'Zonal Thresholds Table' parameter contains path to a table "
                                "or a URL to a feature service.")
            },
            {
                'name': 'zval',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Target Value Field Name",
                'description': ("Name of the field containing the target value to which an input pixel gets remapped. "
                                "If left unspecified--or if the field value is null--remapped pixel values are set "
                                "to the 'Default Target Value'. "
                                "This is only applicable if the 'Zonal Thresholds Table' parameter contains path to a table "
                                "or a URL to a feature service.")
            },
            {
                'name': 'background',
                'dataType': 'numeric',
                'value': 0,
                'required': False,
                'displayName': "Background Value",
                'description': ("The initial pixel value of the output raster--before input pixels are remapped.")
            },
            {
                'name': 'defzval',
                'dataType': 'numeric',
                'value': 255,
                'required': False,
                'displayName': "Default Target Value",
                'description': ("The default remap/target value of threshold. "
                                "This is the value of the output pixel if either the 'Target Value Field Name' "
                                "parameter is left unspecified or if the target value of the corresponding "
                                "zonal threshold is left unspecified in the Zonal Thresholds Table.")
            },
            {
                'name': 'where',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Where Clause",
                'description': ("Additional query applied on the Zonal Thresholds Table. "
                                "Only the rows that satisfy this criteria participate in the zonal remapping.")
            },
        ]


    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,
          'invalidateProperties': 2 | 4 | 8,        # invalidate statistics & histogram on the parent dataset.
          'inputMask': False                        # Don't need input raster mask in .updatePixels().
        }


    def updateRasterInfo(self, **kwargs):
        self.ztMap = None
        self.whereClause = None

        ztStr = kwargs.get('ztable', None)
        ztStr = ztStr.strip() if ztStr else "{}"

        try:
            self.ztMap = loadJSON(ztStr) if ztStr else {}
        except ValueError as e:
            self.ztMap = None

        if self.ztMap is None:
            self.ztMap = {}
            self.ztTable = ZonalAttributesTable(tableUri=ztStr,
                                                idField=kwargs.get('zid', None),
                                                attribList=[kwargs.get('zmin', None), 
                                                            kwargs.get('zmax', None), 
                                                            kwargs.get('zval', None)])

        self.background = kwargs.get('background', None)
        self.background = int(self.background) if self.background else 0

        self.defaultTarget = kwargs.get('defzval', None)
        self.defaultTarget = int(self.defaultTarget) if self.defaultTarget else 255
        self.whereClause = kwargs.get('where', None)

        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['colormap'] = ()
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = pixelBlocks['vraster_pixels'][0]

        zoneIds = None
        z = pixelBlocks.get('zraster_pixels', None)
        if z is not None:               # zone raster is optional 
            z = pixelBlocks['zraster_pixels'][0]
            zoneIds = np.unique(z)      #TODO: handle no-data and mask in zone raster

        ZT = self.ztTable.query(idList=zoneIds, 
                                where=self.whereClause, 
                                extent=props['extent'], 
                                sr=props['spatialReference']) if self.ztTable else self.ztMap

        # output pixels initialized to background color
        p = np.full(v.shape, self.background, dtype=props['pixelType'])

        # use zonal thresholds to update output pixels...
        if ZT is not None and len(ZT.keys()):
            for k in (zoneIds if zoneIds is not None else [None]):
                T = ZT.get(k, None)         # k from z might not be in ztMap
                if not T:
                    continue

                for t in T:
                    I = (z == k) if z is not None else np.ones(v.shape, dtype=bool)
                    if t[0] and t[1]:       # min and max are both available
                        I = I & (v > t[0]) & (v < t[1])
                    elif t[0]:
                        I = I & (v > t[0]) 
                    elif t[1]:
                        I = I & (v < t[1])  
                    p[I] = (t[2] if t[2] is not None else self.defaultTarget)

        pixelBlocks['output_pixels'] = p
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Processed'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None     # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
        return keyMetadata
