import numpy as np
from utils import ZonalThresholdsTable
import json

class ZonalRemap():

    def __init__(self):
        self.name = "Zonal Remap"
        self.description = ""
        self.ztMap = {}                        # zonal thresholds { zoneId:(tMin, tMax), ... }
        self.isUrl = False
        self.ztTable = None

    def getParameterInfo(self):
        return [
            {
                'name': 'vr',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "The primary single-band input raster."
            },
            {
                'name': 'zr',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Zone Raster",
                'description': ("The single-band zone raster where each pixel contains "
                                "the zone ID associated with the location.")
            },
            {
                'name': 'zt',
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
            ### TODO: use time field
        ]


    def updateRasterInfo(self, **kwargs):
        self.ztMap = None
        ztStr = kwargs.get('zt', "{}").strip()

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

        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()
        return kwargs
        

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = pixelBlocks['vr_pixels'][0]
        z = pixelBlocks['zr_pixels'].astype('u1', copy=False)[0]

        uniqueIds = np.unique(z)

        # if zonal threshold table is defined:
        #   - request dictionary for IDs not previously seen
        #   - update ztMap
        if self.ztTable:
            zoneIds = list(set(uniqueIds) - set(self.ztMap.keys()))
            self.ztMap.update(self.ztTable.query(zoneIds))

        # output's all ones to begin with
        p = np.ones_like(v, 'u1')

        # use zonal thresholds to update output pixels...
        for k in uniqueIds:
            t = self.ztMap.get(k, None)                 # k from z might not be in ztMap
            if not t:
                continue

            if t[0] and t[1]:                           # min and max are both available
                I = (v < t[0]) | (v > t[1])
            else:
                I = (v < t[0]) if t[0] else (v > t[1])  # either min or max is available
            
            # all pixels where zoneID is k, which are out of range, set to outValue or 0
            p[(z == k) & I] = (t[3] if t[3] is not None else 0)

        pixelBlocks['output_pixels'] = p.astype(props['pixelType'], copy=False)
        return pixelBlocks
