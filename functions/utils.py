__all__ = ['getTraceFunction']

def getTraceFunction():
    ctypes = __import__('ctypes')
    trace = ctypes.windll.kernel32.OutputDebugStringA
    trace.argtypes = [ctypes.c_char_p]
    return trace


def computeMapExtents(tlc, shape, props):
    nRows, nCols = shape if len(shape) == 2 else shape[1:]      # dimensions of request pixel block
    e, w, h = props['extent'], props['width'], props['height']  # dimensions of parent raster
    dX, dY = (e[2]-e[0])/w, (e[3]-e[1])/h                       # cell size of parent raster
    xMin, yMax = e[0]+tlc[0]*dX, e[3]-tlc[1]*dY                 # top-left corner of request on map
    return (xMin, yMax-nRows*dY, xMin+nCols*dX, yMax)           # extents of request on map
 

def isProductVersionOK(productInfo, major, minor, build): 
    v = productInfo['major']*1.e+10 + int(0.5+productInfo['minor']*10)*1.e+6 + productInfo['build']
    return v >= major*1e+10 + minor*1e+7 + build


def getProj():
    pyproj = __import__('pyproj')
    pyproj.
