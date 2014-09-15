import numpy as np


class VineyardAnalysis():

    def __init__(self):
        self.name = "Vineyard Suitability Analysis Function"
        self.description = "This function computes vineyard suitability given elevation, slope, aspect, and soil-type rasters."
       

    def getParameterInfo(self):
        return [
            {
                'name': 'elevation',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Elevation Raster',
                'description': "The primary single-band raster where pixel values represent elevation in meters."
            },
            {
                'name': 'slope',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Slope Raster',
                'description': "A single-band raster where pixel values represent slope."
            },
            {
                'name': 'aspect',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': 'Aspect Raster',
                'description': "A single-band raster where pixel values represent aspect."
            },
            {
                'name': 'soiltype',
                'dataType': 'raster',
                'value': None,
                'required': False,
                'displayName': 'Soil Type Raster',
                'description': "A single-band thematic raster where pixel values represent soil type."
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
        kwargs['output_info']['noData'] = np.array([0], 'u1')
        return kwargs


    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        elev = np.array(pixelBlocks['elevation_pixels'], 'f4')
        slope = np.array(pixelBlocks['slope_pixels'], 'f4')
        aspect = np.array(pixelBlocks['aspect_pixels'], 'f4')
        #soil = np.array(pixelBlocks['soiltype_pixels'], 'i8')
        
        E = (elev > 30).astype('u1') & (elev < 400).astype('u1')
        S = (slope > 5).astype('u1') & (slope < 60).astype('u1')
        A = (aspect > 0).astype('u1') & (aspect < 200).astype('u1')
        pixelBlocks['output_pixels'] = (E + S + A).astype(props['pixelType'])
        
        return pixelBlocks


    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'VineyardSuitability'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'VineyardSuitability'
        return keyMetadata
