import numpy as np
import utils


class SelectByPixelSize():

    def __init__(self):
        self.name = "Select by Pixel Size"
        self.description = "This function returns pixels associated with one of two input rasters based on the request resolution."
        self.threshold = 0.0
        self.trace = utils.getTraceFunction()
        self.projection = utils.Projection()
    
        
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
                'displayName': "Cell Size Threshold (meters)",
                'description': "The cell size threshold (in meters) that controls which of the two input rasters contributes pixels to the output."
            },
        ]


    def getConfiguration(self, **scalars):
        return { 
            'inputMask': True 
        }

        
    def updateRasterInfo(self, **kwargs):
        io, ir1, ir2 = kwargs['output_info'], kwargs['r1_info'], kwargs['r2_info']

        c1, c2 = ir1['cellSize'], ir2['cellSize']
        self.threshold = kwargs.get('threshold', 0.0)
        if self.threshold <= 0.0:
            self.threshold = np.mean((np.mean(c1), np.mean(c2)))

        io['bandCount'] = min(ir1['bandCount'], ir2['bandCount'])
        io['cellSize'] = (.5*(c1[0]+c2[0]), .5*(c1[1]+c2[1]))
        io['statistics'] = () 
        io['histogram'] = ()
        io['resampling'] = True
        return kwargs
        
        
    def selectRasters(self, tlc, shape, props):
        e, w, h = props['extent'], props['width'], props['height']
        (x1, x2), (y1, y2) = self.projection.transform(props['spatialReference'], 3857, (e[0], e[2]), (e[1], e[3]))
        c = .5*(.5*abs(x2-x1) + .5*abs(y2-y1))
        return ('r1', ) if c < self.threshold else ('r2', )
                

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        self.trace("Trace|SelectByPixelSize.updatePixels.1|request-raster: {0}|\n".format(props))
        e, w, h = props['extent'], props['width'], props['height']
        (x1, x2), (y1, y2) = self.projection.transform(props['spatialReference'], 3857, (e[0], e[2]), (e[1], e[3]))
        c = .5*(.5*abs(x2-x1) + .5*abs(y2-y1))

        rasterId = 1 + int(c >= self.threshold)
        p = pixelBlocks['r{0}_pixels'.format(rasterId)].copy()
        m = pixelBlocks['r{0}_mask'.format(rasterId)].copy()

        iB = 1 if p.ndim == 2 else p.shape[0]
        oB = 1 if len(shape) == 2 else shape[0]
        if iB < oB:
            raise Exception("Number of bands of the request exceed that of the input raster.")

        s = ()
        if iB > 1: s = (0 if oB == 1 else slice(oB), )
        s += (slice(None), slice(None))

        self.trace("Trace|SelectByPixelSize.updatePixels|request-pixel-size: {0}|output-shape: {1}|\n".format(c, s))
        pixelBlocks['output_pixels'] = p[s].squeeze().astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = m[s].squeeze().astype('u1', copy=False)


        self.trace("Trace|SelectByPixelSize.updatePixels.2|input: {0}|output: {1}|\n".format(p[0], pixelBlocks['output_pixels'][0]))
        return pixelBlocks

