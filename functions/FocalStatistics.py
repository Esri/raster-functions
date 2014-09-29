import numpy as np
import ctypes


class FocalStatistics():

    def __init__(self):
        self.name = "Focal Statistics"
        self.description = ""
        self.factor = 1.0
        self.emit = ctypes.windll.kernel32.OutputDebugStringA
        self.emit.argtypes = [ctypes.c_char_p]

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': ""
            },
            {
                'name': 'factor',
                'dataType': 'numeric',
                'value': 1.0,
                'required': True,
                'displayName': "Sampling Factor",
                'description': ""
            },
        ]


    def getConfiguration(self, **scalars):
        self.factor = scalars.get('factor', 1.0)
        return { 
            'samplingFactor': self.factor,
            'inputMask': True 
        }

        
    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['resampling'] = True
        kwargs['output_info']['cellSize'] = tuple(np.multiply(kwargs['raster_info']['cellSize'], self.factor))
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()

        self.emit("Trace|FocalStatistics.UpdateRasterInfo|{0}\n".format(kwargs))
        return kwargs
        

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        s = slice(None, None, self.factor)
        p = pixelBlocks['raster_pixels']
        m = pixelBlocks['raster_mask']

        pixelBlocks['output_pixels'] = p[s, s].astype(props['pixelType'])
        pixelBlocks['output_mask'] = m[s, s].astype('u1')

        self.emit("Trace|Request Raster|{0}\n".format(props))
        self.emit("Trace|Request Size|{0}\n".format(shape))
        return pixelBlocks

