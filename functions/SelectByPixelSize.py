import numpy as np
import utils


class SelectByPixelSize():

    def __init__(self):
        self.name = "Select by Pixel Size"
        self.description = "This function returns pixels associated with one of two input rasters based on the request resolution."
        self.threshold = 0.0
        self.trace = utils.getTraceFunction()

        
    def getParameterInfo(self):
        return [
            {
                'name': 'r1',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster 1",
                'description': ("The raster that's returned when request cell size is lower than the 'Cell Size Threshold'. "
                                "A lower cell size value implies finer resolution.")
            },
            {
                'name': 'r2',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster 2",
                'description': ("The raster that's returned when request cell size is higher than or equal to the 'Cell Size Threshold'. "
                                "A higher cell size value implies coarser resolution.")
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
        c1, c2 = kwargs['r1_info']['cellSize'], kwargs['r2_info']['cellSize']
        self.threshold = kwargs.get('threshold', 0.0)
        if self.threshold <= 0.0:
            self.threshold = np.mean((np.mean(c1), np.mean(c2)))

        oi = kwargs['output_info']
        oi['bandCount'] = min(kwargs['r1_info']['bandCount'], kwargs['r2_info']['bandCount'])
        oi['cellSize'] = (.5*(c1[0]+c2[0]), .5*(c1[1]+c2[1]))
        oi['resampling'] = True
        oi['statistics'] = () 
        oi['histogram'] = ()
        return kwargs
        
        
    def selectRasters(self, tlc, shape, props):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])
        return ('r1', ) if v < self.threshold else ('r2', )
                

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        cellSize = props['cellSize']
        v = 0.5 * (cellSize[0] + cellSize[1])
        rasterId = 1 + int(v >= self.threshold)
        p = pixelBlocks['r{0}_pixels'.format(rasterId)].copy()
        m = pixelBlocks['r{0}_mask'.format(rasterId)].copy()

        iB = 1 if p.ndim == 2 else p.shape[0]
        oB = 1 if len(shape) == 2 else shape[0]
        if iB < oB:
            raise Exception("Number of bands of the request exceed that of the input raster.")

        s = ()
        if iB > 1: s = (0 if oB == 1 else slice(outBands), )
        s += (slice(None), slice(None))

        self.trace("Trace|SelectByPixelSize.updatePixels|request-pixel-size: {0}|output-shape: {1}|\n".format(v, s))
        pixelBlocks['output_pixels'] = p[s].squeeze().astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = m[s].squeeze().astype('u1', copy=False)


        self.trace("Trace|SelectByPixelSize.updatePixels.2|input: {0}|output: {1}|\n".format(p[0], pixelBlocks['output_pixels'][0]))
        return pixelBlocks

