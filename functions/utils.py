__all__ = ['isProductVersionOK',
           'computePixelBlockExtents',
           'computeCellSize',
           'Projection',
           'Trace']


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
