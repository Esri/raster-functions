__all__ = ['isProductVersionOK',
           'computePixelBlockExtents',
           'computeCellSize',
           'Projection',
           'Trace',
           'ZonalThresholdsTable',]


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- #


def isProductVersionOK(productInfo, major, minor, build):
    v = productInfo['major']*1.e+10 + int(0.5+productInfo['minor']*10)*1.e+6 + productInfo['build']
    return v >= major*1e+10 + int(0.5+minor*10)*1.e+6 + build


def computePixelBlockExtents(tlc, shape, props):
    nRows, nCols = shape if len(shape) == 2 else shape[1:]      # dimensions of request pixel block
    e, w, h = props['extent'], props['width'], props['height']  # dimensions of parent raster
    dX, dY = (e[2]-e[0])/w, (e[3]-e[1])/h                       # cell size of parent raster
    xMin, yMax = e[0]+tlc[0]*dX, e[3]-tlc[1]*dY                 # top-left corner of request on map
    return (xMin, yMax-nRows*dY, xMin+nCols*dX, yMax)           # extents of request on map


def computeCellSize(props, sr=None, proj=None):
    e, w, h = props['extent'], props['width'], props['height']  # dimensions of parent raster
    if sr is None:
        return (e[2]-e[0])/w, (e[3]-e[1])/h                     # cell size of parent raster

    if proj is None:
        proj = Projection()                                     # reproject extents

    (xMin, yMin) = proj.transform(props['spatialReference'], sr, e[0], e[1])
    (xMax, yMax) = proj.transform(props['spatialReference'], sr, e[2], e[3])
    return (xMax-xMin)/w, (yMax-yMin)/h                         # cell size of parent raster


def isGeographic(s):
    arcpy = __import__('arcpy')
    sr = arcpy.SpatialReference()
    sr.loadFromString(str(s) if isinstance(s, (str, int, long)) else s.exportToString())
    return bool(sr.type == 'Geographic' and sr.angularUnitName)


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- #


class Projection():
    def __init__(self):
        self.arcpy = __import__('arcpy')
        self.inSR, self.outSR = None, None

    def transform(self, inSR, outSR, x, y):
        if self.inSR != inSR:
            self.inSR = self.createSR(inSR)
        if self.outSR != outSR:
            self.outSR = self.createSR(outSR)
    
        p = self.arcpy.PointGeometry(self.arcpy.Point(x, y), self.inSR, False, False)
        q = p.projectAs(self.outSR)
        return q.firstPoint.X, q.firstPoint.Y

    def createSR(self, s):
        sr = self.arcpy.SpatialReference()
        sr.loadFromString(str(s) if isinstance(s, (str, int, long)) else s.exportToString())
        return sr


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- #


class Trace():
    def __init__(self):
        ctypes = __import__('ctypes')
        self.trace = ctypes.windll.kernel32.OutputDebugStringA
        self.trace.argtypes = [ctypes.c_char_p]
        self.c_char_p = ctypes.c_char_p

    def log(self, s):
        self.trace(self.c_char_p(s.encode('utf-8')))
        return s

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- #


class ZonalThresholdsTable():
    def __init__(self, tableUri, 
                 idField="ObjectID", 
                 minField="MinValue", 
                 maxField="MaxValue", 
                 outField="OutValue"):
        if idField is None:
            raise Exception("TODO");

        if tableUri is None:
            raise Exception("TODO");

        self.tableUri = tableUri
        self.idField  = idField.lower()  if idField  else None
        self.minField = minField.lower() if minField else None
        self.maxField = maxField.lower() if maxField else None
        self.outField = outField.lower() if outField else None
        
        self.fieldList = [a for a in [self.idField, self.minField, self.maxField, self.outField] 
                          if (a is not None and len(a))]
        self.fieldCSV = ",".join(self.fieldList)

        self.queryUrl = None    # indicator of remote URL vs local table
        s = tableUri.lower()
        if s.startswith('http://') or s.startswith('https://'):
            self.queryUrl = tableUri + ('/query' if tableUri[-1] != '/' else 'query')
            self.urllib = __import__('urllib')
            self.json = __import__('json')
        else:
            self.arcpy = __import__('arcpy')


    def query(self, idList=[], where=None, extent=None, sr=None):
        if self.queryUrl:
            return self._queryFeatureService(self, idList, where, extent, sr)
        else:
            return self._queryTable(self, idList, where, extent, sr)

    def _queryTable(self, idList=[], where=None, extent=None, sr=None):
        T = {}
        with self.arcpy.da.SearchCursor(tableName, fieldNames) as cursor:
            for row in cursor:
                if row[0]:
                    T.update({row[0]: (row[1], row[2], row[3])})
        return T

    def _queryFeatureService(self, idList=[], where=None, extent=None, sr=None):
        p = {'f': 'json', 'returnGeometry': 'false'}
        p.update({'outFields': self.fieldCSV})
        
        w = None
        if idList and len(idList):
            w = "{0} IN ({1})".format(self.idField, ",".join(str(z) for z in idList))

        w = "( {0} ){1}( {2} )".format(w if w else "", 
                                       " AND " if w and where and len(where) else "", 
                                       where if where else "")
        if w and len(w): 
            p.update({'where': w})

        if extent and len(extent) == 4 and sr and isinstance(sr, int): 
            p.update({'geometryType': 'esriGeometryEnvelope',
                      'geometry': {'xmin': extent[0], 
                                   'ymin': extent[1],
                                   'xmax': extent[2],
                                   'ymax': extent[3]},
                      'inSR': {'latestWkid': int(sr)},
                      'spatialRel': 'esriSpatialRelEnvelopeIntersects'})

        T = {}
        r = self.urllib.urlopen(self.queryUrl, self.urllib.urlencode(p)).read()

        responseJO = self.json.loads(r)
        featuresJA = responseJO.get('features', None)
        if featuresJA is not None:
            for featureJO in featuresJA:
                attrJO = featureJO.get('attributes', None)
                if attrJO is not None:
                    id = attrJO.get(self.idField, None)
                    if id:
                        minValue = attrJO.get(self.minField, None)
                        maxValue = attrJO.get(self.maxField, None)
                        outValue = attrJO.get(self.outField, None)
                        T.update({id: (minValue, maxValue, outValue)})
        return T
