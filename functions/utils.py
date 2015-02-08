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
 
