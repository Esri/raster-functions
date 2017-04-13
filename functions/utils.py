#------------------------------------------------------------------------------
# Copyright 2016 Esri
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

__all__ = ['isProductVersionOK',
           'computePixelBlockExtents',
           'computeCellSize',
           'Projection',
           'Trace',
           'ZonalAttributesTable',
           'projectCellSize',]


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- #

degreeToMeter = 111319.49079327357264771338267056
pi = 3.14159265358979323846

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

def projectCellSize(cellSize, inSR, outSR, proj=None):
    inSRS = proj.createSR(inSR)
    outSRS = proj.createSR(outSR)
    if isGeographic(inSR) and isGeographic(outSR):
        x =  cellSize[0] * (inSRS.radiansPerUnit/outSRS.radiansPerUnit)
        y = cellSize[1] * (inSRS.radiansPerUnit/outSRS.radiansPerUnit)

    elif not isGeographic(inSR) and not isGeographic(outSR):
        x = cellSize[0] * (inSRS.metersPerUnit/outSRS.metersPerUnit)
        y = cellSize[1] * (inSRS.metersPerUnit/outSRS.metersPerUnit)

    elif isGeographic(inSR):
        factor1 = inSRS.radiansPerUnit
        factor1 = factor1/pi*180
        factor2 = outSRS.metersPerUnit
        if factor2 is None:
            factor2 = 1
        x = cellSize[0] * (factor1 * degreeToMeter)/factor2
        y = cellSize[1] * (factor1 * degreeToMeter)/factor2 

    elif isGeographic(outSR):
        factor2 = outSRS.radiansPerUnit
        factor2 = pi/180/factor2
        factor1 = inSRS.metersPerUnit
        if factor1 is None:
            factor1 = 1
        x = cellSize[0] * (factor2/degreeToMeter) * factor1
        y = cellSize[1] * (factor2/degreeToMeter) * factor1

    return x, y


def isGeographic(s):
    arcpy = __import__('arcpy')
    sr = arcpy.SpatialReference()
    sr.loadFromString(str(s) if isinstance(s, (str, int, long)) else s.exportToString())
    return bool(sr.type == 'Geographic' and sr.angularUnitName)


def loadJSON(s):
    if s is None:
        return None

    json = __import__('json')
    from os import path

    if path.exists(s):
        with open(s) as f:
            return json.load(f)
    else:
        return json.loads(s)


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

# TODO: support early termination (when only one row is needed), like in non-zonal rasterize attributes.
class ZonalAttributesTable():
    def __init__(self, tableUri, idField=None, attribList=None):
        if tableUri is None:
            raise Exception("TODO");

        self.tableUri = tableUri
        self.idField, self.idFI = (idField.lower(), 0) if idField else (None, None)
        self.attribList = attribList or []

        k = 0
        self.fi, self.queryFields = [], []
        for a in self.attribList:
            if a is not None and len(a):
                self.queryFields.append(a)  
                self.fi.append(k)
                k = k + 1
            else: 
                self.fi.append(None)

        if self.idField: 
            self.fi = [k+1 if k is not None else None for k in self.fi]

        self.tupleSize = len(self.fi)
        self.queryFields = ([self.idField] if self.idField else []) + self.queryFields

        if not len(self.queryFields):
            raise Exception("TODO")
         
        self.fieldCSV = ",".join(self.queryFields)

        self.arcpy = None
        self.queryUrl = None    # indicator of remote URL vs local table
        s = tableUri.lower()
        if s.startswith('http://') or s.startswith('https://'):
            self.queryUrl = tableUri + ('/query' if tableUri[-1] != '/' else 'query')
            self.urllib = __import__('urllib')
            self.json = __import__('json')

    def query(self, idList=[], where=None, extent=None, sr=None):
        if self.arcpy is None:
            self.arcpy = __import__('arcpy')
        w = self._constructWhereClause(idList, where)
        if not self.queryUrl:
            return self._queryTable(w)
        else:
            return self._queryFeatureService(w, extent, sr)

    def _queryTable(self, where=None):
        T = {}
        with self.arcpy.da.SearchCursor(self.tableUri, self.queryFields, where_clause=where) as cursor:
            for row in cursor:
                I = []
                for k in range(self.tupleSize):
                    I.append(row[self.fi[k]] if self.fi[k] is not None else None)
                self._addAttributes(T, row[self.idFI] if self.idFI is not None else None, tuple(I))
        return T

    def _queryFeatureService(self, where=None, extent=None, sr=None):
        p = {'f': 'json', 'returnGeometry': 'false'}
        p.update({'outFields': self.fieldCSV})
        
        if where and len(where): 
            p.update({'where': where})

        if extent and len(extent) == 4 and sr:
            _sr = sr
            if not isinstance(sr, self.arcpy.SpatialReference) and isinstance(sr, (str, int, long)):
                _sr = self.arcpy.SpatialReference()
                _sr.loadFromString(str(sr))

            if _sr.factoryCode > 0:
                p.update({'inSR': {'latestWkid': _sr.factoryCode}})
            else:
                p.update({'inSR': {'wkt': _sr.exportToString()}})

            p.update({'geometryType': 'esriGeometryEnvelope',
                      'geometry': {'xmin': extent[0], 
                                   'ymin': extent[1],
                                   'xmax': extent[2],
                                   'ymax': extent[3]},
                      'spatialRel': 'esriSpatialRelEnvelopeIntersects'})

        T = {}
        r = self.urllib.urlopen(self.queryUrl, self.urllib.urlencode(p)).read()

        responseJO = self.json.loads(r)
        featuresJA = responseJO.get('features', None)
        if featuresJA is not None:
            for featureJO in featuresJA:
                attrJO = featureJO.get('attributes', None)
                if attrJO is not None:
                    A = []
                    for z in self.attribList:
                        A = A + [attrJO.get(z, None)]
                    self._addAttributes(T, attrJO.get(self.idField, None), tuple(A))
        return T

    def _constructWhereClause(self, idList=[], where=None):
        w1 = "( " + where + " )" if where and len(where) else None
        if self.idField and idList is not None and len(idList): 
            w2 = "( {0} IN ({1}) )".format(self.idField, ",".join(str(z) for z in idList)) 
        else:
            w2 = None

        return "{0}{1}{2}".format(w1 if w1 else "", 
                                  " AND " if w1 and w2 else "", 
                                  w2 if w2 else "")

    def _addAttributes(self, T, zoneId, attribValues):
        T[zoneId] = T.get(zoneId, []) + [attribValues]
