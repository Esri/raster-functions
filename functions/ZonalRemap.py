import numpy as np
from utils import ZonalThresholdsTable, Trace
import json

class ZonalRemap():

    def __init__(self):
        self.name = "Zonal Remap"
        self.description = ""
        self.ztMap = {}                        # zonal thresholds { zoneId:[zMin,zMax,zVal], ... }
        self.isUrl = False
        self.ztTable = None
        self.background = 0
        self.defaultTarget = 255
        self.trace = Trace()

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
                'required': True,
                'displayName': "Zone Raster",
                'description': ("The single-band zone raster where each pixel contains "
                                "the zone ID associated with the location.")
            },
            {
                'name': 'ztable',
                'dataType': 'string',
                'value': None,
                'required': True,
                'displayName': "Zonal Thresholds",
                'description': ("The threshold map specified as a JSON string, "
                                "a path to a local feature class or table, "
                                "or a URL to a feature service layer.")
            },
            {
                'name': 'zid',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Zone ID Field Name",
                'description': "TODO"
            },
            {
                'name': 'zmin',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Minimum Value Field Name",
                'description': "TODO"
            },
            {
                'name': 'zmax',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Maximum Value Field Name",
                'description': "TODO"
            },
            {
                'name': 'zval',
                'dataType': 'string',
                'value': None,
                'required': False,
                'displayName': "Target Value Field Name",
                'description': "TODO"
            },
            {
                'name': 'background',
                'dataType': 'numeric',
                'value': 0,
                'required': False,
                'displayName': "Background Value",
                'description': "TODO"
            },
            {
                'name': 'defzval',
                'dataType': 'numeric',
                'value': 255,
                'required': False,
                'displayName': "Default Target Value",
                'description': "TODO"
            },

            ### TODO: use time field
        ]


    def updateRasterInfo(self, **kwargs):
        self.ztMap = None
        ztStr = kwargs.get('ztable', "{}").strip()

        try:
            self.ztMap = json.loads(ztStr) if ztStr else {}
        except ValueError as e:
            self.ztMap = None

        if self.ztMap is None:
            self.ztMap = {}
            self.ztTable = ZonalThresholdsTable(ztStr,
                                                kwargs.get('zid', None),
                                                kwargs.get('zmin', None),
                                                kwargs.get('zmax', None),
                                                kwargs.get('zval', None))

        self.background = int(kwargs.get('background', 0))
        self.defaultTarget = int(kwargs.get('defzval', 255))
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()
        return kwargs
        

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = pixelBlocks['vraster_pixels'][0]
        z = pixelBlocks['zraster_pixels'].astype('u1', copy=False)[0]

        uniqueIds = np.unique(z)    #TODO: handle no-data and mask in zone raster

        # if zonal threshold table is defined:
        #   - request dictionary for IDs not previously seen
        #   - update ztMap
        if self.ztTable:
            zoneIds = list(set(uniqueIds) - set(self.ztMap.keys()))
            if len(zoneIds):
                self.ztMap.update(self.ztTable.query(zoneIds))
            self.trace.log("Trace|ZonalRemap.updatePixels|ZT:{0}|ZoneIDs:{1}|".format(str(self.ztMap), str(zoneIds)))

        # output's all ones to begin with
        p = np.full(v.shape, self.background, dtype='u1')

        # use zonal thresholds to update output pixels...
        for k in uniqueIds:
            t = self.ztMap.get(k, None)                     # k from z might not be in ztMap
            if not t:
                continue

            I = (z == k)
            if t[0] and t[1]:                               # min and max are both available
                I = I & (v > t[0]) & (v < t[1])
            else:
                I = I & (v > t[0]) if t[0] else (v < t[1])  # either min or max is available
            
            # all pixels where zoneID is k, which are out of range, set to outValue or 0
            p[I] = (t[2] if t[2] is not None else self.defaultTarget)

        pixelBlocks['output_pixels'] = p.astype(props['pixelType'], copy=False)
        return pixelBlocks
