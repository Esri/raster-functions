import numpy as np
import ctypes


class SelectByPixelSize():

    def __init__(self):
        self.name = "Select by Pixel Size"
        self.description = "This function returns pixels associated with one of two input rasters based on the request resolution."
        self.threshold = 0.0
        self.inBands1, self.inBands2, self.outBands = 1, 1, 1
        self.emit = ctypes.windll.kernel32.OutputDebugStringA
        self.emit.argtypes = [ctypes.c_char_p]

        
    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster 1",
                'description': "The raster that's returned when request cell size is lower than the 'Cell Size Threshold'. A lower cell size value implies finer resolution."
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster 2",
                'description': "The raster that's returned when request cell size is higher than or equal to the 'Cell Size Threshold'. A higher cell size value implies coarser resolution."
            },
            {
                'name': 'threshold',
                'dataType': 'numeric',
                'value': 0.0,
                'required': True,
                'displayName': "Cell Size Threshold",
                'description': "The cell size threshold that controls which of the two input rasters contributes pixels to the output."
            },
        ]


    def getConfiguration(self, **scalars):
        return { 
            'inputMask': True 
        }

        
    def updateRasterInfo(self, **kwargs):
        self.threshold = kwargs.get('threshold', 0.0)
        if self.threshold <= 0.0:
            self.threshold = np.mean((np.mean(kwargs['r1_info']['cellSize']), np.mean(kwargs['r2_info']['cellSize'])))

        self.inBands1 = kwargs['r1_info']['bandCount']
        self.inBands2 = kwargs['r2_info']['bandCount']
        kwargs['output_info']['bandCount'] = min(self.inBands1, self.inBands2)
        kwargs['output_info']['resampling'] = True
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()

        self.emit("Trace|Threshold cell-size|{0}\n".format(self.threshold))
        self.emit("Trace|output_info|{0}\n".format(kwargs['output_info']))
        return kwargs
        
        
    def selectRasters(self, tlc, shape, props):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])
        if v < self.threshold:
            return ('r1',)
        else: return ('r2',)


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])
        self.emit("Trace|Request cell-size|{0}\n".format(v))
        
        if v < self.threshold:
            sPixels = 'r1_pixels'
            sMask = 'r1_mask'
            nBands = self.inBands1
        else:
            sPixels = 'r2_pixels'
            sMask = 'r2_mask'
            nBands = self.inBands2

        if self.outBands == nBands:
            p = pixelBlocks[sPixels]
            m = pixelBlocks[sMask]
        else:
            p = pixelBlocks[sPixels][0:self.outBands, :, :]
            m = pixelBlocks[sMask][0:self.outBands, :, :]

        pixelBlocks['output_pixels'] = p.astype(props['pixelType'])
        pixelBlocks['output_mask'] = m.astype('u1')
        return pixelBlocks

