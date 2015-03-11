import numpy as np
import utils


class FocalStatistics():

    def __init__(self):
        self.name = "Focal Statistics"
        self.description = ""
        self.factor = 1.0
        self.trace = utils.Trace()

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
            # 'padding': self.factor,
            'inputMask': True 
        }

        
    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['resampling'] = False
        kwargs['output_info']['cellSize'] = tuple(np.multiply(kwargs['raster_info']['cellSize'], self.factor))
        kwargs['output_info']['statistics'] = () 
        kwargs['output_info']['histogram'] = ()

        self.trace.log("Trace|FocalStatistics.updateRasterInfo|{0}\n".format(kwargs))
        return kwargs
        

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        s = slice(None, None, max(1, self.factor))
        p = pixelBlocks['raster_pixels']
        m = pixelBlocks['raster_mask']

        if len(p.shape) <= 2 or p.shape[0] == 1:
            outP = p[s, s]
            outM = m[s, s]
        else:
            outP = p[:, s, s]
            outM = m[:, s, s]

        pixelBlocks['output_pixels'] = outP.astype(props['pixelType'])
        pixelBlocks['output_mask'] = outM.astype('u1')

        self.trace.log("Trace|FocalStatistics.updatePixels|Request Raster|{0}\n".format(props))
        self.trace.log("Trace|FocalStatistics.updatePixels|Request Size|{0}\n".format(shape))
        return pixelBlocks

