import numpy as np


class VineyardAnalysis():

    def __init__(self):
        self.name = "Vineyard Analysis Function"
        self.description = ""
       
    def getParameterInfo(self):
        return [
            {
                'name': 'elevation',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Elevation Raster',
                'description': ""
            },
            {
                'name': 'slope',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Slope Raster',
                'description': ""
            },
            {
                'name': 'aspect',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Aspect Raster',
                'description': ""
            },
            {
                'name': 'soiltype',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Soil Type Raster',
                'description': ""
            },            
        ]        

       
    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 2 | 4 | 8,       # inherit all but the pixel type from the input raster
          'invalidateProperties': 2 | 4 | 8,    # reset any statistics and histogram that might be held by the parent dataset (because this function modifies pixel values). 
          'inputMask': True                     # We need the input raster mask in .updatePixels(). 
        }


    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1  
        kwargs['output_info']['pixelType'] = 'u1'
        kwargs['output_info']['statistics'] = ({'minimum': 0, 'maximum': 3}, )
        kwargs['output_info']['noData'] = 0
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        elev = np.array(pixelBlocks['elevation_pixels'], dtype='float')
        slope = np.array(pixelBlocks['slope_pixels'], dtype='float')
        aspect = np.array(pixelBlocks['aspect_pixels'], dtype='float')
        soil = np.array(pixelBlocks['soiltype_pixels'], dtype='int8')
        
        E = elev > 30 & elev < 400
        S = slope > 5 & slope < 60
        A = aspect > 0 & aspect < 200
        pixelBlocks['output_pixels'] = (E + S + A).astype(int)
        
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'Vineyard'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Vineyard'
        return keyMetadata
