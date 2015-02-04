from scipy import ndimage
import numpy as np
import math 
import Hillshade

class TintedHillshade():

    def __init__(self):
        self.name = "Tinted Hillshade Function"
        self.description = ""
        self.h = Hillshade()

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Input Raster",
                'description': "",
            },
            {
                'name': 'elevation',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Elevation Raster",
                'description': "",
            },
        ]


    def getConfiguration(self, **scalars): 
        return {
          'inheritProperties': 4 | 8,           # inherit everything but the pixel type (1) and NoData (2)
          'invalidateProperties': 2 | 4 | 8,    # invalidate these aspects because we are modifying pixel values and updating key properties.
          'padding': 1,                         # one extra on each each of the input pixel block
          'inputMask': True                     # we need the input mask in .updatePixels()
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = ({'minimum': 0., 'maximum': 255.}, )
        kwargs['output_info']['histogram'] = ()
        kwargs['output_info']['colormap'] = ()

        e = kwargs['elevation_info'] 
        if e['bandCount'] != 1:
            raise Exception("Input elevation has more than one band. Only single-band elevation datasets are supported")

        if kwargs['raster_info']['bandCount'] != 3:
            raise Exception("Input raster is not RGB.")

        self.h.prepare(zFactor=1., cellSize=e['cellSize'], sr=e['spatialReference'])        
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        v = np.array(pixelBlocks['raster_pixels'], dtype='f4', copy=False)
        e = np.array(pixelBlocks['elevation_pixels'], dtype='f4', copy=False)
        m = np.array(pixelBlocks['elevation_mask'], dtype='u1', copy=False)

        dx, dy = self.h.computeGradients(v)
        hsBlock = self.h.computeHillshade(dx, dy)

        outBlock[0] = 0.5(v[0] + e)
        outBlock[1] = 0.5(v[1] + e)
        outBlock[2] = 0.5(v[2] + e)

        pixelBlocks['output_pixels'] = outBlock[1:-1, 1:-1].astype(props['pixelType'], copy=False)

        # cf: http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html
        pixelBlocks['output_mask'] = \
            m[:-2,:-2]  & m[1:-1,:-2]  & m[2:,:-2]  \
          & m[:-2,1:-1] & m[1:-1,1:-1] & m[2:,1:-1] \
          & m[:-2,2:]   & m[1:-1,2:]   & m[2:,2:]

        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                             # dataset-level properties           
            keyMetadata['datatype'] = 'Processed'       # outgoing dataset is now 'Processed'
        elif bandIndex == 0:                            # properties for the first band
            keyMetadata['wavelengthmin'] = None         # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'TintedHillshade'
        return keyMetadata

