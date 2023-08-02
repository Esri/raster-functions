import numpy as np
import os
import arcpy
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["BLIS_NUM_THREADS"] = "1"
#import datetime
#from datetime import timedelta
#import sys

#import os
#import pickle

#debug_logs_directory = r'C:\PROJECTS\SWEEDEN\debug'

# Based on QA Band - https://landsat.usgs.gov/collectionqualityband
LANDSAT_4_7_CLEAR_PIX_VALS = [672, 676, 680, 684]
LANDSAT_8_CLEAR_PIX_VALS = [20480, 20484, 20512, 23552]#[2720, 2724, 2728, 2732]
LANDSAT_CLEAR_PIX_VALS = LANDSAT_4_7_CLEAR_PIX_VALS + LANDSAT_8_CLEAR_PIX_VALS
FILTER_VAL = -3001

def apply_mask(tct_stack, bqa_stack, clear_code):
    tct_stack[~np.isin(bqa_stack, clear_code)] = -3001
    return tct_stack.astype('float')

class LandsatMedianPixelComposite:

    def __init__(self):
        self.name = 'Landsat Median Pixel Composite'
        self.description = 'This raster function computes the median pixel value from a collection of overlapping ' \
                           'Landsat images. The input mosaic dataset must be a collection of Landsat images. The ' \
                           'raster function reads the collection, filters out cloud pixels, and then, where' \
                           'pixels overlap, computes the median pixel value. This raster function is intended to be ' \
                           'used in order to create images that are indicative of what you should see from ' \
                           'Landsat on a cloud free day for a specific month or season.'


    def getParameterInfo(self):
        return [
            {
                'name': 'rasters',
                'dataType': 'rasters',
                'value': None,
                'required': True,
                'displayName': 'Rasters',
                'description': 'The collection of overlapping rasters to aggregate.',
            }
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 4 | 8,  # 1 | 2 |  inherit everything but the pixel type (1) and NoData (2)
            'invalidateProperties': 2 | 4,  # invalidate histogram and statistics because we are modifying pixel values
            'inputMask': True,  # need raster mask of all input rasters in .updatePixels().
            'resampling': False  # process at native resolution
        }

    def updateRasterInfo(self, **kwargs):
        # outStats = {'minimum': -1, 'maximum': 1}
        # self.outBandCount = 6

        # The 32-bit float thing works with Copy Raster
        kwargs['output_info']['pixelType'] = 'f4'  # output pixels are floating-point values
        #kwargs['output_info']['histogram'] = ()  # no statistics/histogram for output raster specified
        #kwargs['output_info']['statistics'] = ()  # outStatsTuple
        #kwargs['output_info']['bandCount'] = self.outBandCount   # number of output bands.

        self.qa_band_num = 7
        polygon = None
        if 'rasters_info' in kwargs:
            rasters_info = kwargs['rasters_info']
            nRasters = len(rasters_info)
            i = 0
            while i < nRasters:
                raster_info = rasters_info[i]
                i = i+1
                e = raster_info['extent']
                xMin = e[0]
                yMin = e[1]
                xMax = e[2]
                yMax = e[3]

                # Create a polygon geometry
                array = arcpy.Array([arcpy.Point(xMin, yMin),
                     arcpy.Point(xMin, yMax),
                     arcpy.Point(xMax, yMax),
                     arcpy.Point(xMax, yMin)])

                srs_in = arcpy.SpatialReference(raster_info['spatialReference'])
                e = arcpy.Polygon(array, spatial_reference = srs_in)
                e = e.projectAs(arcpy.SpatialReference(kwargs['output_info']['spatialReference']))
                projected_cords = (e.extent.XMin, e.extent.YMin, e.extent.XMax, e.extent.YMax)
                if polygon is not None:
                    polygon = e | polygon
                else:
                    polygon = e


        if polygon is not None:
            xMin = polygon.extent.XMin
            yMin = polygon.extent.YMin
            xMax = polygon.extent.XMax
            yMax = polygon.extent.YMax

            dx = kwargs['output_info']['cellSize'][0]
            dy = kwargs['output_info']['cellSize'][1]

            nCols = int((xMax - xMin) / dx + 0.5);
            nRows = int((yMax - yMin) / dy + 0.5);
            yMin =  yMax - (nRows * dy)
            xMax = xMin + (nCols * dx)
            kwargs['output_info']['extent'] = (xMin, yMin, xMax, yMax)
            #kwargs['output_info']['spatialReference'] = polygon.spatialReference
            #kwargs['output_info']['nativeSpatialReference'] = polygon.spatialReference
            kwargs['output_info']['nativeExtent'] = (xMin, yMin, xMax, yMax)

        kwargs['output_info']['bandCount'] = self.qa_band_num-1  # number of output bands.
        #kwargs['output_info']['pixelType'] = 'f4'           # output pixels are floating-point values
        kwargs['output_info']['histogram'] = ()             # no statistics/histogram for output raster specified
        kwargs['output_info']['statistics'] = ()            # outStatsTuple

        return kwargs

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        return keyMetadata

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        #fname = 'updatePixels_{:%Y_%b_%d_%H_%M_%S}_t.txt'.format(datetime.datetime.now())
        #filename = os.path.join(debug_logs_directory, fname)
        #file = open(filename, "w")
        #file.write("File Open.\n")
        #file.write("Before t_vals.\n")
        #file.close()

        #file.write("After t_vals.\n")
        #file.close()

        # debug
        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(t_vals, open(pickle_filename[:-4] + 'pix_time.p', "wb"))
        #file.write("After pickle dump.\n")

        #file.write(str(len(t_vals)) + "\n")
        #file.write("After pix_time.\n")

        pix_blocks = pixelBlocks['rasters_pixels']
        pix_array = np.asarray(pix_blocks)

        # debug
        #pickle_filename = os.path.join(debug_logs_directory, fname)
        #pickle.dump(pix_blocks, open(pickle_filename[:-4] + 'pix_blocks.p', "wb"))

        pix_array_filtered = pix_array

        #file.write("filtered.\n")

        pix_array_dim = pix_array_filtered.shape
        num_bands = pix_array_dim[1] - 1
        num_squares_x = pix_array_dim[2]
        num_squares_y = pix_array_dim[3]

        try:
            qa_band_ind = self.qa_band_num - 1

            bqa_stack = pix_array_filtered[:, qa_band_ind, :, :]

            #file.write("qa stack.\n")

            pix_array_filtered = pix_array_filtered[:, 0:qa_band_ind, :, :]

            bqa_stack = np.expand_dims(bqa_stack, 1)

            bqa_stack = np.repeat(bqa_stack, qa_band_ind, 1)

            pix_array_filtered = apply_mask(pix_array_filtered.astype('f4'), bqa_stack, LANDSAT_CLEAR_PIX_VALS)

            masked_pix_array = np.ma.masked_where(pix_array_filtered == FILTER_VAL, pix_array_filtered)
            mdata = np.ma.filled(masked_pix_array, np.nan)

            median = np.nanmedian(mdata,axis=0)
            mask = np.ones((num_bands, num_squares_x, num_squares_y))

        except:
            median = np.ones((num_bands, num_squares_x, num_squares_y))
            mask = np.ones((num_bands, num_squares_x, num_squares_y))

        pixelBlocks['output_mask'] = mask.astype('u1', copy=False)
        pixelBlocks['output_pixels'] = median.astype(props['pixelType'], copy=False)

        #file.write("DONE.")
        #file.close()

        return pixelBlocks
