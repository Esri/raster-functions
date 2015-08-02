import numpy as np


class FishHabitatSuitability():

    def __init__(self):
        self.name = "Fish Habitat Suitability Function"
        self.description = "Computes fish habitat suitability by depth."
        self.depth = 0.0

    def getParameterInfo(self):
        return [
            {
                'name': 'temperature',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayname': "Surface Temperature Raster",
                'description': "A single-band raster where values represent surface temperature in Celsius.",
            },
            {
                'name': 'salinity',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayname': "Surface Salinty Raster",
                'description': "A single-band raster where values represent surface salinity in PSU.",
            },
            {
                'name': 'depth',
                'dataType': 'numeric',
                'value': self.depth,
                'required': True,
                'displayname': "Ocean Depth",
                'description': "A numeric value representing ocean depth in meters.",
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'inheritProperties': 2 | 4 | 8,     # inherit everything but the pixel type (1)
            'invalidateProperties': 2 | 4 | 8   # invalidate these aspects because we are modifying pixels and key metadata
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1
        kwargs['output_info']['pixelType'] = 'f4'
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 1.0}, )
        kwargs['output_info']['histogram'] = ()
        self.depth = abs(float(kwargs['depth']))

        # piece-wise linear parameters for depth...
        d = self.depth
        dMinA = 0
        dMinP = 2
        dMaxP = 11
        dMaxA = 20

        if d < dMinA or d > dMaxA:
            d = 0.0
        elif d <= dMinP:
            d = (d - dMinA) / (dMinP - dMinA)
        elif d >= dMaxP:
            d = (d - dMaxA) / (dMaxP - dMaxA)
        else:
            d = 1

        self.depth = d
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        t = np.array(pixelBlocks['temperature_pixels'], dtype='f4', copy=False)
        s = np.array(pixelBlocks['salinity_pixels'], dtype='f4', copy=False)

        # piece-wise linear parameters for temperature...
        tMinA = 17.99
        tMinP = 26.37
        tMaxP = 29.15
        tMaxA = 33.35

        np.putmask(t, t <= tMinP, (t - tMinA) / (tMinP - tMinA))
        np.putmask(t, t >= tMaxP, (t - tMaxA) / (tMaxP - tMaxA))
        np.putmask(t, (t > tMinP) & (t < tMaxP), 1)
        np.putmask(t, t < 0, 0)

        # piece-wise linear parameters for salinity...
        sMinA = 28.81
        sMinP = 32.27
        sMaxP = 35.81
        sMaxA = 36.79

        np.putmask(s, s <= sMinP, (s - sMinA) / (sMinP - sMinA))
        np.putmask(s, s >= sMaxP, (s - sMaxA) / (sMaxP - sMaxA))
        np.putmask(s, (s > sMinP) & (s < sMaxP), 1)
        np.putmask(s, s < 0, 0)

        # get overall probability by tying all conditions
        pixelBlocks['output_pixels'] = np.array(t * s * self.depth).astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'FishHabitatSuitability'
        return keyMetadata
