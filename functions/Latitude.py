import numpy as np
import pickle


class Latitude():
    def __init__(self):
        self.name = 'Latitude Raster'
        self.description = 'Replace NULL values in a raster with a user defined value.'

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': 'Single Band Raster',
                'required': True,
                'displayName': 'Input Raster',
                'description': 'Input Raster'
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 1 | 2 | 4 | 8,  # inherit everything but the pixel type (1) and NoData (2)
            # 'invalidateProperties': 1 | 2 | 4 | 8,      # invalidate histogram and statistics because we are modifying pixel values
            'resampling': False
        }

    def updateRasterInfo(self, **kwargs):
        # repeat stats for all output raster bands
        # kwargs['output_info']['statistics'] = tuple(outStats for i in range(self.out_band_count))
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ()

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        # https://scriptndebug.wordpress.com/2014/11/24/latitudelongitude-of-each-pixel-using-python-and-gdal/
        # GDAL affine transform parameters, According to gdal documentation
        # xoff/yoff are image left corner,
        # a/e are pixel wight/height and
        # b/d is rotation and is zero if image is north up.

        pix_array = np.asarray(pixelBlocks['raster_pixels'])
        cellsize = props['cellSize']
        extent = props['extent']
        res = np.ones(pix_array.shape)

        cellsize = cellsize
        rcs = shape
        rows = rcs[2]
        cols = rcs[1]
        top_left_x = extent[0]
        top_left_y = extent[3]

        yp = [top_left_y - cellsize[1] * y for y in range(0, cols)]

        for x in range(0, rows):
            res[0, :, x] = yp

        #pickle.dump([pix_array, cellsize, tlc, shape, extent], open(r'C:\Users\greg6750\Documents\USFS\objs.p', 'wb'))

        # def pixel2coord(x, y):
        #     """Returns global coordinates from pixel x, y coords"""
        #     #xp = a * x + b * y + xoff
        #     #yp = d * x + e * y + yoff
        #     xp = cellsize[0] * x + tlc[0]
        #     yp = cellsize[1] * y + tlc[1]
        #
        #     return xp, yp
        #
        # for row in range(0, shape[0]):
        #     for col in range(0, shape[1]):
        #         pixel2coord(col, row)
        #
        # val = [cellsize[0] * x + tlc[0] for x in range(0, shape[0])]
        # res[:,x] =

        mask = np.ones(pix_array.shape)
        pixelBlocks['output_mask'] = mask.astype('u1', copy=False)
        pixelBlocks['output_pixels'] = res.astype(props['pixelType'], copy=True)

        return pixelBlocks


