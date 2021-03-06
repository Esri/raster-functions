import numpy as np

class HeatIndex():

    def __init__(self):
        self.name = "Heat Index Function"
        self.description = ("This function combines ambient air temperature and relative humidity "
                            "to return apparent temperature.")
        self.tempUnits = 'f'
        self.hiUnits = 'f'

    def getParameterInfo(self):
        return [
            {
                'name': 'temperature',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Temperature Raster",
                'description': ("A single-band raster where pixel values represent ambient air temperature "
                                "in Fahrenheit, Celsius, or Kelvin.")
            },
            {
                'name': 'units',
                'dataType': 'string',
                'value': 'Fahrenheit',
                'required': True,
                'domain': ('Celsius', 'Fahrenheit', 'Kelvin'),
                'displayName': "Temperature Units",
                'description': "The unit of measurement associated with the input temperature raster."
            },
            {
                'name': 'rh',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Relative Humidity Raster",
                'description': ("A single-band raster where pixel values represent relative humidity as "
                                "a percentage value between 0 and 100.")
            },
            {
                'name': 'outunits',
                'dataType': 'string',
                'value': 'Fahrenheit',
                'required': True,
                'domain': ('Celsius', 'Fahrenheit', 'Kelvin'),
                'displayName': "Output Heat Index Units",
                'description': "The unit of measurement associated with the output heat-index raster."
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,               # inherit all but the pixel type and NoData from the input raster
          'invalidateProperties': 2 | 4 | 8,        # invalidate statistics & histogram on the parent dataset because we modify pixel values. 
          'inputMask': False                        # Don't need input raster mask in .updatePixels(). Simply use the inherited NoData. 
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1      # output is a single band raster
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 180}, )  # we know something about the stats of the outgoing HeatIndex raster. 
        kwargs['output_info']['histogram'] = ()     # we know nothing about the histogram of the outgoing raster.
        kwargs['output_info']['pixelType'] = 'f4'   # bit-depth of the outgoing HeatIndex raster based on user-specified parameters

        self.tempUnits = kwargs.get('units', None)
        self.tempUnits = (self.tempUnits or 'Fahrenheit').lower()[0] 

        self.hiUnits = kwargs.get('outunits', None)
        self.hiUnits = (self.hiUnits or 'Fahrenheit').lower()[0] 

        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        t = np.array(pixelBlocks['temperature_pixels'], dtype='f4', copy=False)[0].flatten()
        r = np.array(pixelBlocks['rh_pixels'], dtype='f4', copy=False)[0].flatten()

        # transform t to Fahrenheit
        if self.tempUnits == 'k':
            t = (1.8 * t) - 459.67
        elif self.tempUnits == 'c':
            t = (1.8 * t) + 32.

        tr = t * r
        rr = r * r
        tt = t * t
        ttr = tt * r
        trr = t * rr
        ttrr = ttr * r

        # compute simple heat index
        H = .5 * (t + 61. + (((t - 68.) * 1.2) + (r * .094)))   # simple heat index
        a = ((H + t) / 2.) > 80

        # compute heat-index using Rothfusz's full regression model
        fullHI = (-42.379 + (2.04901523 * t) + (10.14333127 * r) - (0.22475541 * tr) 
                    - (6.83783e-3 * tt) - (5.481717e-2 * rr) + (1.22874e-3 * ttr) 
                    + (8.5282e-4 * trr) - (1.99e-6 * ttrr))

        # apply adjustments
        c = a & ((r < 13) & (t >= 80.) & (t <= 112))
        fullHI[c] -= (((13. - r[c]) / 4.) * np.sqrt((17. - np.abs(t[c]-95.)) / 17.))

        c = a & ((r > 85) & (t >= 80.) & (t <= 87))
        tc = t[c]
        fullHI[c] += (((tc - 85.) / 10.) * ((87. - tc) / 5.))

        # use full heat-index conditionally
        H[a] = fullHI[a]

        # transform HI to desired output units
        if self.hiUnits == 'k':
            H = (H + 459.67) / 1.8
        elif self.hiUnits == 'c':
            H = (H - 32.) / 1.8

        pixelBlocks['output_pixels'] = H.astype(props['pixelType'], copy=False).reshape(shape)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                                     # update dataset-level key metadata
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'HeatIndex'
            if self.hiUnits == 'k':
                keyMetadata['unit'] = 'esriKelvin'
            elif self.hiUnits == 'c':
                keyMetadata['unit'] = 'esriCelsius'
            else:
                keyMetadata['unit'] = 'esriFahrenheit'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'HeatIndex'
        return keyMetadata

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1] Steadman, Robert G. "The assessment of sultriness. Part I: 
        A temperature-humidity index based on human physiology and clothing science." 
        Journal of Applied Meteorology 18.7 (1979): 861-873.

    [2] Steadman, Robert G. "The assessment of sultriness. Part II: 
        effects of wind, extra radiation and barometric pressure on apparent temperature." 
        Journal of Applied Meteorology 18.7 (1979): 874-885.

    [3] National Weather Service. "NWS Heat Index."
        http://www.nws.noaa.gov/om/heat/heat_index.shtml
        http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
"""
